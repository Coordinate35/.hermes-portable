#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Piper TTS 快速调用脚本（供 Hermes Agent 使用）
默认使用小雅音色
"""

import sys
import subprocess
import os
from pathlib import Path

PIPER_DIR = Path("/home/coordinate35/hermes_data/piper")
DEFAULT_MODEL = PIPER_DIR / "models" / "zh_CN-xiao_ya-medium.onnx"
VENV_PYTHON = PIPER_DIR / ".venv" / "bin" / "python3"

def synthesize(text: str, output_path: str = None, model_path: str = None) -> str:
    """
    合成语音，返回音频文件路径
    """
    if output_path is None:
        output_path = "/tmp/piper_output.wav"
    if model_path is None:
        model_path = str(DEFAULT_MODEL)
    
    # 使用 venv 中的 piper
    env = os.environ.copy()
    env["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    cmd = [
        str(VENV_PYTHON), "-c",
        f"""
import sys
sys.path.insert(0, str({repr(str(PIPER_DIR / ".venv" / "lib" / "python3.11" / "site-packages"))}))
from piper import voice as piper_voice
import wave

v = piper_voice.PiperVoice.load({repr(model_path)})
with wave.open({repr(output_path)}, "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(22050)
    v.synthesize({repr(text)}, wav_file)
"""
    ]
    
    # 更简单的方式：直接调用 piper CLI
    cmd = [
        "bash", "-c",
        f"cd {PIPER_DIR} && source .venv/bin/activate && "
        f"HF_ENDPOINT=https://hf-mirror.com "
        f'echo {repr(text)} | piper --model {model_path} --output_file {output_path}'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"Piper error: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"TTS failed: {result.stderr}")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 piper_tts.py '\u4f60好，世界'")
        sys.exit(1)
    
    text = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "/tmp/piper_output.wav"
    path = synthesize(text, output)
    print(path)
