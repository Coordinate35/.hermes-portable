#!/usr/bin/env python3
"""
MeloTTS wrapper for Hermes Agent
Usage: python3 melo_tts.py "text to speak" /path/to/output.mp3
"""
import sys
import os
import time

# 自动检测并激活虚拟环境
VENV_PYTHON = os.path.expanduser("~/hermes_data/melotts/.venv/bin/python3")
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

from melo.api import TTS

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 melo_tts.py <text> <output_path>", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    output_path = sys.argv[2]

    # HuggingFace 国内镜像
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

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
