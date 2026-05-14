#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAV -> WeChat 语音消息转换
尝试多种格式，找出微信能识别为语音气泡的方案
"""

import sys
import os
import subprocess
from pathlib import Path

PIPER_DIR = Path("/home/coordinate35/hermes_data/piper")
VENV_PYTHON = PIPER_DIR / ".venv" / "bin" / "python3"

def wav_to_pcm(wav_path: str, pcm_path: str, sample_rate: int = 16000) -> str:
    """WAV -> PCM s16le mono"""
    cmd = [
        "ffmpeg", "-y", "-i", wav_path,
        "-ar", str(sample_rate), "-ac", "1", "-f", "s16le",
        pcm_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return pcm_path

def pcm_to_silk(pcm_path: str, silk_path: str, sample_rate: int = 16000) -> str:
    """PCM -> SILK"""
    env = os.environ.copy()
    env["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    code = f"""
import sys
sys.path.insert(0, str({repr(str(PIPER_DIR / ".venv" / "lib" / "python3.11" / "site-packages"))}))
import pilk
pilk.encode({repr(pcm_path)}, {repr(silk_path)}, {sample_rate})
"""
    subprocess.run([str(VENV_PYTHON), "-c", code], env=env, check=True)
    return silk_path

def add_tencent_header(silk_path: str, output_path: str) -> str:
    """
    微信语音文件通常有一个腾讯前缀头。
    格式: 0x02 + 'SILK' 或其他魔数
    """
    with open(silk_path, 'rb') as f:
        silk_data = f.read()
    
    # 微信语音常见的前缀是 0x02 字节，然后是 SILK 标识
    # 但不同版本可能不同，这里尝试几种
    
    # 方案A: 纯 SILK
    with open(output_path + ".pure.silk", 'wb') as f:
        f.write(silk_data)
    
    # 方案B: 添加 0x02 前缀（某些旧版微信）
    with open(output_path + ".tencent.silk", 'wb') as f:
        f.write(b'\x02' + silk_data)
    
    # 方案C: 添加 AMR 文件头（某些版本用 AMR 伪装）
    # AMR 头: #!AMR\n
    with open(output_path + ".amr", 'wb') as f:
        f.write(b'#!AMR\n' + silk_data)
    
    return output_path

def convert(wav_path: str, base_output: str = "/tmp/wechat_voice"):
    """完整转换流程"""
    pcm_path = base_output + ".pcm"
    silk_path = base_output + ".silk"
    
    # Step 1: WAV -> PCM
    wav_to_pcm(wav_path, pcm_path)
    
    # Step 2: PCM -> SILK
    pcm_to_silk(pcm_path, silk_path)
    
    # Step 3: 生成多种格式变体
    add_tencent_header(silk_path, base_output)
    
    print(f"转换完成，输出文件:")
    for ext in [".pure.silk", ".tencent.silk", ".amr"]:
        p = base_output + ext
        if os.path.exists(p):
            size = os.path.getsize(p)
            print(f"  {p} ({size} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wav_to_wechat_voice.py <wav_file>")
        sys.exit(1)
    convert(sys.argv[1])
