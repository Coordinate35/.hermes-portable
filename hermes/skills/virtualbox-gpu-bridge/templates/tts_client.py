#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatTTS 客户端 - 运行于虚拟机内，调用宿主机的 ChatTTS GPU 服务。
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

# 宿主机服务地址（VirtualBox NAT 模式下，10.0.2.2 是宿主机地址）
DEFAULT_HOST = "10.0.2.2"
DEFAULT_PORT = 5000


def make_request(path, data=None, method="GET", host=DEFAULT_HOST, port=DEFAULT_PORT):
    """发起 HTTP 请求"""
    url = f"http://{host}:{port}{path}"
    
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(), resp.headers.get_content_type()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), None
    except Exception as e:
        print(f"[错误] 请求失败: {e}")
        sys.exit(1)


def check_health(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """检查服务状态"""
    status, body, _ = make_request("/health", host=host, port=port)
    if status == 200:
        info = json.loads(body)
        print("═" * 40)
        print("服务状态")
        print("═" * 40)
        print(f"  状态:      {info['status']}")
        print(f"  CUDA:      {'可用' if info['cuda_available'] else '不可用'}")
        print(f"  GPU 设备:   {info['cuda_device'] or 'N/A'}")
        print(f"  模型加载:  {'已加载' if info['model_loaded'] else '未加载'}")
        if info['load_error']:
            print(f"  加载错误:  {info['load_error']}")
        print("═" * 40)
        return info
    else:
        print(f"[错误] 服务返回 {status}")
        print(body.decode("utf-8", errors="replace"))
        return None


def synthesize(text, output="output.wav", audio_seed=42, temperature=0.3, 
               top_P=0.7, top_K=20, fmt="wav", host=DEFAULT_HOST, port=DEFAULT_PORT):
    """语音合成"""
    print(f"[合成] 正在合成: {text[:40]}...")
    print(f"       等待 GPU 推理中，请稍候...")
    
    data = {
        "text": text,
        "audio_seed": audio_seed,
        "temperature": temperature,
        "top_P": top_P,
        "top_K": top_K,
        "format": fmt
    }
    
    status, body, ctype = make_request("/tts", data=data, method="POST", host=host, port=port)
    
    if status == 200 and ctype and "audio" in ctype:
        with open(output, "wb") as f:
            f.write(body)
        print(f"[成功] 音频已保存: {output} ({len(body)} 字节)")
        return output
    else:
        print(f"[错误] 服务返回 {status}")
        try:
            err = json.loads(body)
            print(f"       {err.get('error', body.decode('utf-8', errors='replace'))}")
        except:
            print(body.decode("utf-8", errors="replace"))
        return None


def main():
    parser = argparse.ArgumentParser(description="ChatTTS 客户端")
    parser.add_argument("text", nargs="?", default=None, help="要合成的文本")
    parser.add_argument("-o", "--output", default="output.wav", help="输出文件路径")
    parser.add_argument("--host", default=DEFAULT_HOST, help="服务器地址")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务器端口")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--temp", type=float, default=0.3, help="温度 (0-1)")
    parser.add_argument("--format", default="wav", choices=["wav", "mp3"], help="输出格式")
    parser.add_argument("--health", action="store_true", help="只检查服务状态")
    
    args = parser.parse_args()
    
    if args.health:
        check_health(host=args.host, port=args.port)
        return
    
    if not args.text:
        print("用法: python3 tts_client.py '你好，世界' ")
        print("或:    python3 tts_client.py --health")
        sys.exit(1)
    
    # 先检查健康状态
    info = check_health(host=args.host, port=args.port)
    if not info:
        sys.exit(1)
    
    if not info.get("model_loaded"):
        print("[提示] 模型尚未加载，第一次请求会自动加载，需要几分钟...")
    
    # 执行合成
    result = synthesize(
        args.text,
        output=args.output,
        audio_seed=args.seed,
        temperature=args.temp,
        fmt=args.format,
        host=args.host,
        port=args.port
    )
    
    if result:
        print(f"\n✓ 完成！音频文件: {result}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
