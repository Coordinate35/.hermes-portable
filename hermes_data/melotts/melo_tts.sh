#!/bin/bash
set -e
source "$HOME/hermes_data/melotts/.venv/bin/activate"
export HF_ENDPOINT=https://hf-mirror.com
python3 "$HOME/hermes_data/melotts/melo_tts.py" "$1" "$2"
