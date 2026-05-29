#!/bin/bash
# TTS 音频清理：删除 7 天前的临时音频文件
# 覆盖：
#   1. /tmp/*.wav  /tmp/*.mp3            — Windows/MeloTTS/临时合成
#   2. ~/.hermes/audio_cache/*.mp3       — Edge TTS 缓存
#   3. ~/hermes_data/ebooks/*/audio_cache/*.wav  — 听书系统的章节音频缓存（按书隔离，自动覆盖未来新加的书）

TMP_WAV=$(find /tmp -maxdepth 1 -type f -name "*.wav" -mtime +7 2>/dev/null)
TMP_MP3=$(find /tmp -maxdepth 1 -type f -name "*.mp3" -mtime +7 2>/dev/null)
CACHE_MP3=$(find ~/.hermes/audio_cache -maxdepth 1 -type f -name "*.mp3" -mtime +7 2>/dev/null)
# 听书音频：递归到每本书的 audio_cache/ 子目录
# -mindepth 3 防止误删上层目录的其他文件（路径深度 = ebooks/<book>/audio_cache/<file>）
EBOOK_WAV=$(find ~/hermes_data/ebooks -mindepth 3 -type f -name "*.wav" -mtime +7 2>/dev/null)

count=0
[ -n "$TMP_WAV" ] && echo "$TMP_WAV" | xargs -r rm -f && count=$((count + $(echo "$TMP_WAV" | wc -l)))
[ -n "$TMP_MP3" ] && echo "$TMP_MP3" | xargs -r rm -f && count=$((count + $(echo "$TMP_MP3" | wc -l)))
[ -n "$CACHE_MP3" ] && echo "$CACHE_MP3" | xargs -r rm -f && count=$((count + $(echo "$CACHE_MP3" | wc -l)))
[ -n "$EBOOK_WAV" ] && echo "$EBOOK_WAV" | xargs -r rm -f && count=$((count + $(echo "$EBOOK_WAV" | wc -l)))

if [ "$count" -gt 0 ]; then
    echo "已清理 $count 个超过 7 天的音频文件"
fi
# 没有需要清理的文件时，输出为空 → 静默
