# -*- coding: utf-8 -*-
"""
ChatTTS HTTP API Server
运行于 Windows 宿主机，提供语音合成 HTTP 服务，供虚拟机调用。
"""

import os
import io
import base64
import tempfile
import time
import json
from pathlib import Path

from flask import Flask, request, jsonify, send_file, Response

app = Flask(__name__)

# 全局模型实例
chat_tts = None
model_loaded = False
load_error = None

# 路径配置
CACHE_DIR = Path(__file__).parent / "chattts_cache"
CACHE_DIR.mkdir(exist_ok=True)
SPEAKER_DIR = CACHE_DIR / "speakers"
SPEAKER_DIR.mkdir(exist_ok=True)

def load_model():
    """懒加载 ChatTTS 模型，只在第一次请求时初始化"""
    global chat_tts, model_loaded, load_error
    
    if model_loaded:
        return True
    if load_error:
        return False
    
    try:
        import ChatTTS
        import torch
        import torchaudio
        
        print("[信息] 正在初始化 ChatTTS 模型，第一次会自动下载（约 3-4GB）...")
        print("[信息] 这可能需要几分钟，请耐心等待...")
        
        chat_tts = ChatTTS.Chat()
        chat_tts.load(compile=False)  # compile=True 可加速但首次启动更慢
        
        model_loaded = True
        print("[信息] ✓ 模型加载成功！GPU: " + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"))
        return True
        
    except Exception as e:
        load_error = str(e)
        print(f"[错误] ✗ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    import torch
    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "load_error": load_error,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cache_dir": str(CACHE_DIR)
    })


@app.route("/speakers", methods=["GET"])
def list_speakers():
    """列出已保存的音色"""
    speakers = []
    for f in SPEAKER_DIR.glob("*.pt"):
        speakers.append({
            "id": f.stem,
            "path": str(f),
            "size": f.stat().st_size
        })
    return jsonify({"speakers": speakers, "count": len(speakers)})


@app.route("/tts", methods=["POST"])
def tts():
    """
语音合成接口

Body (JSON):
    {
        "text": "要合成的文本",
        "speaker_id": "可选，使用已保存的音色",
        "temperature": 0.3,      // 随机性，0-1，越低越稳定
        "top_P": 0.7,            // nucleus sampling
        "top_K": 20,             // top-k sampling
        "audio_seed": 42,        // 音频随机种子（用来复现音色）
        "text_seed": 42,         // 文本处理随机种子
        "speed": 1.0,            // 速度倍率（ChatTTS 本身不直接支持，需后处理）
        "refine_text": true,     // 是否优化文本
        "format": "wav"          // 返回格式: wav 或 mp3
    }

Response:
    文件下载 (audio/wav 或 audio/mpeg)
"""
    if not load_model():
        return jsonify({"error": f"模型未加载: {load_error}"}), 500
    
    try:
        import torch
        import torchaudio
        import numpy as np
        
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        
        if not text:
            return jsonify({"error": "text 字段不能为空"}), 400
        
        # 参数解析
        speaker_id = data.get("speaker_id", None)
        temperature = float(data.get("temperature", 0.3))
        top_P = float(data.get("top_P", 0.7))
        top_K = int(data.get("top_K", 20))
        audio_seed = data.get("audio_seed", None)
        text_seed = data.get("text_seed", None)
        refine_text = bool(data.get("refine_text", True))
        fmt = data.get("format", "wav").lower()
        
        if fmt not in ("wav", "mp3"):
            fmt = "wav"
        
        # 随机种子
        if audio_seed is not None:
            torch.manual_seed(int(audio_seed))
        
        # 音色加载
        speaker_path = None
        if speaker_id:
            sp = SPEAKER_DIR / f"{speaker_id}.pt"
            if sp.exists():
                speaker_path = str(sp)
        
        # 构建参数
        params_infer_code = {
            "prompt": f"[speed_{data.get('speed', 1.0)}]" if data.get('speed', 1.0) != 1.0 else "",
            "temperature": temperature,
            "top_P": top_P,
            "top_K": top_K,
        }
        
        params_refine_text = {
            "prompt": "",
            "top_P": top_P,
            "top_K": top_K,
            "temperature": temperature,
        }
        
        # 执行合成
        print(f"[合成] 文本: {text[:50]}... | speaker: {speaker_id} | seed: {audio_seed}")
        start = time.time()
        
        if speaker_path:
            # 使用已保存的音色
            speaker_emb = torch.load(speaker_path)
            wavs = chat_tts.infer(
                [text],
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
                do_text_normalization=True,
                do_homophone_replacement=True,
                use_decoder=True,
            )
        else:
            wavs = chat_tts.infer(
                [text],
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
                do_text_normalization=True,
                do_homophone_replacement=True,
                use_decoder=True,
            )
        
        duration = time.time() - start
        print(f"[完成] 耗时 {duration:.2f}s")
        
        # 转换为音频文件
        wav = wavs[0]
        if isinstance(wav, np.ndarray):
            wav_tensor = torch.from_numpy(wav).unsqueeze(0)
        else:
            wav_tensor = wav.unsqueeze(0) if wav.dim() == 1 else wav
        
        # 确保是 [channels, samples] 格式
        if wav_tensor.dim() == 1:
            wav_tensor = wav_tensor.unsqueeze(0)
        
        suffix = ".mp3" if fmt == "mp3" else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            temp_path = f.name
        
        torchaudio.save(temp_path, wav_tensor, 24000, format="mp3" if fmt == "mp3" else "wav")
        
        mimetype = "audio/mpeg" if fmt == "mp3" else "audio/wav"
        return send_file(temp_path, mimetype=mimetype, as_attachment=False)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/tts/save_speaker", methods=["POST"])
def save_speaker():
    """
生成并保存一个新音色

Body:
    {"speaker_id": "my_voice", "audio_seed": 42, "text_seed": 42}
"""
    if not load_model():
        return jsonify({"error": f"模型未加载: {load_error}"}), 500
    
    try:
        data = request.get_json(force=True)
        speaker_id = data.get("speaker_id", "").strip()
        audio_seed = int(data.get("audio_seed", 42))
        
        if not speaker_id:
            return jsonify({"error": "speaker_id 不能为空"}), 400
        
        import torch
        torch.manual_seed(audio_seed)
        
        # ChatTTS 随机抽取一个说话人特征
        speaker_emb = chat_tts.sample_random_speaker()
        
        save_path = SPEAKER_DIR / f"{speaker_id}.pt"
        torch.save(speaker_emb, str(save_path))
        
        return jsonify({
            "success": True,
            "speaker_id": speaker_id,
            "path": str(save_path),
            "audio_seed": audio_seed
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("   ChatTTS HTTP Server")
    print("=" * 50)
    print("本机访问: http://127.0.0.1:5000")
    print("局域网访问: http://<宿主机IP>:5000")
    print("虚拟机访问: http://10.0.2.2:5000")
    print("=" * 50)
    print()
    print("首次请求 /tts 时会自动加载模型...")
    print()
    
    # 监听 0.0.0.0 让虚拟机也能访问
    app.run(host="0.0.0.0", port=5000, threaded=True)
