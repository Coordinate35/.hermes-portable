#!/usr/bin/env python3
"""音频预合成脚本：取下一批段落，TTS 合成 combined wav。

用法:
  precompose.py --book "<书名>" [--peek-offset 1] [--count 5]

行为:
  1. 调 read.py --peek 取段（默认偏移1批=取"下一批"）
  2. 拼接段落文本
  3. 检查目标 wav 是否已存在且 > 10KB → 命中直接返回
  4. 调 win_tts.sh 一次性合成
  5. 字符 > 2500 时 fallback：分批 TTS + ffmpeg concat（暂未实现，仅打印警告）

输出: JSON 到 stdout
  { status: ok|cached|skipped|error, audio_path, chapter, paragraph_range, char_count }

设计目的: 在 agent 后台运行，提前合成下一批音频，让用户说"继续"时秒发缓存。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
READ_PY = SCRIPT_DIR / 'read.py'
WIN_TTS = Path.home() / '.hermes/scripts/win_tts.sh'
EBOOKS_ROOT = Path.home() / 'hermes_data/ebooks'
TTS_MAX_CHARS = 2500


def emit(payload: dict):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--peek-offset', type=int, default=1,
                    help='偏移：1=合成下一批（默认），0=合成当前批')
    ap.add_argument('--count', type=int, default=5)
    args = ap.parse_args()

    book_dir = EBOOKS_ROOT / args.book
    if not book_dir.exists():
        emit({'status': 'error', 'error': f'书不存在: {args.book}'})
        sys.exit(1)

    cache_dir = book_dir / 'audio_cache'
    cache_dir.mkdir(exist_ok=True)

    # 1. 调 read.py --peek 取段
    cmd = [
        sys.executable, str(READ_PY),
        '--book', args.book,
        '--mode', 'continue',
        '--count', str(args.count),
        '--peek',
        '--peek-offset', str(args.peek_offset),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        emit({'status': 'error', 'error': 'read.py 失败', 'stderr': r.stderr})
        sys.exit(2)

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        emit({'status': 'error', 'error': 'read.py 输出非 JSON', 'raw': r.stdout[:500]})
        sys.exit(2)

    # 全书末尾
    if data.get('is_book_end') and not data.get('paragraphs'):
        emit({'status': 'skipped', 'reason': 'book_end', 'message': '已到全书末尾，无需预合成'})
        return

    paragraphs = data.get('paragraphs', [])
    if not paragraphs:
        emit({'status': 'skipped', 'reason': 'no_paragraphs', 'data': data})
        return

    chapter = data['chapter']
    p_start, p_end = data['paragraph_range']
    p_end_inclusive = p_end - 1

    # 2. 拼接
    combined_text = '\n\n'.join(p['text'] for p in paragraphs)
    char_count = len(combined_text)

    out_name = f'combined_ch{chapter:03d}_p{p_start:03d}-p{p_end_inclusive:03d}.wav'
    out_path = cache_dir / out_name

    # 3. 缓存命中
    if out_path.exists() and out_path.stat().st_size > 10240:
        emit({
            'status': 'cached',
            'audio_path': str(out_path),
            'chapter': chapter,
            'paragraph_range': [p_start, p_end],
            'char_count': char_count,
            'message': '已存在缓存，跳过合成',
        })
        return

    # 4. 字符上限保护
    if char_count > TTS_MAX_CHARS:
        emit({
            'status': 'error',
            'error': f'字符数 {char_count} > {TTS_MAX_CHARS}，需要 fallback 到分批+ffmpeg（暂未实现）',
            'audio_path': None,
            'chapter': chapter,
            'paragraph_range': [p_start, p_end],
        })
        sys.exit(3)

    # 5. 一次性 TTS（走 Windows GPT-SoVITS）
    r = subprocess.run(
        ['bash', str(WIN_TTS), combined_text, str(out_path)],
        capture_output=True, text=True, timeout=180
    )
    if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 10240:
        emit({
            'status': 'error',
            'error': 'win_tts 失败',
            'returncode': r.returncode,
            'stderr': r.stderr,
            'stdout': r.stdout,
            'audio_path': str(out_path) if out_path.exists() else None,
        })
        sys.exit(4)

    emit({
        'status': 'ok',
        'audio_path': str(out_path),
        'chapter': chapter,
        'chapter_title': data.get('chapter_title'),
        'paragraph_range': [p_start, p_end],
        'char_count': char_count,
        'size_bytes': out_path.stat().st_size,
    })


if __name__ == '__main__':
    main()
