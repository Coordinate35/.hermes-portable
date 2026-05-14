#!/bin/bash
# Piper TTS 便捷脚本
# 用法: ./tts.sh "你好，世界" [output.wav]

set -e

TEXT="${1:-你好，这是一段测试语音。}"
OUTPUT="${2:-output.wav}"
MODEL="${MODEL:-$(dirname "$0")/models/zh_CN-xiao_ya-medium.onnx}"

source "$(dirname "$0")/.venv/bin/activate"

echo "[合成] $TEXT"
echo "       → $OUTPUT"

echo "$TEXT" | piper \
    --model "$MODEL" \
    --output_file "$OUTPUT" \
    --sentence-silence 0.2

echo "[完成] 音频已保存: $OUTPUT"
