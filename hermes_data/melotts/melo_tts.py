#!/usr/bin/env python3
"""
MeloTTS wrapper for Hermes Agent
Usage: python3 melo_tts.py "text to speak" /path/to/output.mp3
"""
import sys
import os
import time

# 在 import transformers 之前设置环境变量，确保走国内镜像且离线优先
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "1"  # 模型已缓存，强制离线运行

from melo.api import TTS

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 melo_tts.py <text> <output_path>", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    output_path = sys.argv[2]

    model = TTS(language="ZH", device="cpu")
    speaker_id = model.hps.data.spk2id["ZH"]

    start = time.time()
    model.tts_to_file(
        text,
        speaker_id,
        output_path,
        sdp_ratio=0.2,
        noise_scale=0.6,
        noise_scale_w=0.8,
        speed=1.0,
    )
    elapsed = time.time() - start
    print(f"[MeloTTS] 合成完成: {output_path} ({elapsed:.1f}s)")

if __name__ == "__main__":
    main()
