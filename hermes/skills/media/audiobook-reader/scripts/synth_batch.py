#!/usr/bin/env python3
"""现合成兜底脚本：当 precompose 预热错位/未跑/失败导致缓存未命中时，
agent 用 locate 模式取**指定段范围**的文本，直接调 win_tts 合成 combined wav，
**不动 progress.json**。

适用场景:
  - 上一轮 precompose 用错了 --peek-offset，预合成的不是用户即将要听的批
  - 后台 precompose 还在跑，但用户已经发"继续"且等不了
  - 章节切换边界、第一次跑某本书等冷启动情况

不适用场景:
  - 正常预合成流程（用 precompose.py）
  - 推进进度（用 read.py --mode continue 或 locate）

用法:
  synth_batch.py --book "<书名>" --chapter N --start P [--count 5]

行为:
  1. 调 read.py --mode locate --chapter N --paragraph P --count C
     ⚠️ 这会把 progress 写到 [P, P+C)，**调用者需要确认这不是回退**
     （多数兜底场景下，progress 已经在 ≥ P+C，本调用相当于回滚再前进，
      最终落点不变；但要避免在 progress < P 时误用导致跳跃）
  2. 拼接段落文本（\\n\\n 间隔）
  3. 检查目标 wav 已存在且 > 10KB → 直接返回 cached
  4. 调 win_tts.sh 一次合成到 combined_ch{NNN}_p{P}-p{P+C-1}.wav

输出: JSON 到 stdout
  { status, audio_path, chapter, paragraph_range, char_count }

注意:
  - 文件名是**闭区间** p{start}-p{end-1}，和 precompose / 主流程保持一致
  - read.py paragraph_range 是半开 [start, end)，转换时 end_inclusive = end - 1
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
    ap.add_argument('--chapter', type=int, required=True)
    ap.add_argument('--start', type=int, required=True, help='起始段 index（0-based）')
    ap.add_argument('--count', type=int, default=5)
    args = ap.parse_args()

    book_dir = EBOOKS_ROOT / args.book
    if not book_dir.exists():
        emit({'status': 'error', 'error': f'书不存在: {args.book}'})
        sys.exit(1)

    cache_dir = book_dir / 'audio_cache'
    cache_dir.mkdir(exist_ok=True)

    # 1. 调 read.py locate 取段
    cmd = [
        sys.executable, str(READ_PY),
        '--book', args.book,
        '--mode', 'locate',
        '--chapter', str(args.chapter),
        '--paragraph', str(args.start),
        '--count', str(args.count),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        emit({'status': 'error', 'error': 'read.py 失败', 'stderr': r.stderr})
        sys.exit(2)

    data = json.loads(r.stdout)
    paragraphs = data.get('paragraphs', [])
    if not paragraphs:
        emit({'status': 'error', 'error': 'read.py 返回空段落', 'data': data})
        sys.exit(2)

    p_start, p_end = data['paragraph_range']
    p_end_inclusive = p_end - 1
    chapter = data['chapter']

    combined_text = '\n\n'.join(p['text'] for p in paragraphs)
    char_count = len(combined_text)

    out_name = f'combined_ch{chapter:03d}_p{p_start:03d}-p{p_end_inclusive:03d}.wav'
    out_path = cache_dir / out_name

    # 缓存命中
    if out_path.exists() and out_path.stat().st_size > 10240:
        emit({
            'status': 'cached',
            'audio_path': str(out_path),
            'chapter': chapter,
            'paragraph_range': [p_start, p_end],
            'char_count': char_count,
        })
        return

    if char_count > TTS_MAX_CHARS:
        emit({
            'status': 'error',
            'error': f'字符数 {char_count} > {TTS_MAX_CHARS}，需 ffmpeg 分批兜底',
            'chapter': chapter,
            'paragraph_range': [p_start, p_end],
        })
        sys.exit(3)

    r = subprocess.run(
        ['bash', str(WIN_TTS), combined_text, str(out_path)],
        capture_output=True, text=True, timeout=180
    )
    if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 10240:
        emit({
            'status': 'error',
            'error': 'win_tts 失败',
            'returncode': r.returncode,
            'stderr': r.stderr[:500],
        })
        sys.exit(4)

    emit({
        'status': 'ok',
        'audio_path': str(out_path),
        'chapter': chapter,
        'paragraph_range': [p_start, p_end],
        'char_count': char_count,
        'size_bytes': out_path.stat().st_size,
    })


if __name__ == '__main__':
    main()
