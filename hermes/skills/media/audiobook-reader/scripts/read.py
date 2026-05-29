#!/usr/bin/env python3
"""朗读引擎：从指定位置取若干段，自动更新进度。

用法:
  read.py --book "射雕英雄传"                             # 继续读，默认 5 段
  read.py --book "射雕英雄传" --count 3                    # 继续读 3 段
  read.py --book "射雕英雄传" --mode locate --chapter 5    # 跳到第5回开始读
  read.py --book "射雕英雄传" --mode chapter --chapter 1   # 读整章第1回

输出: JSON 到 stdout
{
  "book": "射雕英雄传",
  "chapter": 1,
  "chapter_title": "第一回 风雪惊变",
  "paragraph_range": [0, 5],
  "paragraphs": [{"index": 0, "text": "...", "cache_name": "ch001_p000.wav"}, ...],
  "next_chapter": 1, "next_paragraph": 5,
  "is_chapter_end": false,
  "is_book_end": false,
  "total_progress_pct": 1.2,
  "audio_cache_dir": "/home/.../audio_cache"
}
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

EBOOKS_ROOT = Path.home() / 'hermes_data' / 'ebooks'


def load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def save_json(p: Path, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def get_chapter_paragraphs(book_dir: Path, chapter_id: int):
    """读章节文件并返回段落数组。"""
    chapters = load_json(book_dir / 'chapters.json')
    if chapter_id < 1 or chapter_id > len(chapters):
        return None, None
    ch = chapters[chapter_id - 1]
    text = (book_dir / ch['file']).read_text(encoding='utf-8')
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return ch, paragraphs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--mode', default='continue', choices=['continue', 'chapter', 'locate'])
    ap.add_argument('--chapter', type=int, default=None)
    ap.add_argument('--paragraph', type=int, default=None)
    ap.add_argument('--count', type=int, default=5, help='连读多少段（默认5）')
    ap.add_argument('--peek', action='store_true',
                    help='预览模式：只取段不更新进度，用于后台预合成')
    ap.add_argument('--peek-offset', type=int, default=0,
                    help='peek 模式下的偏移量：0=当前进度位置，1=下一批位置（continue 模式专用）')
    args = ap.parse_args()

    book_dir = EBOOKS_ROOT / args.book
    if not book_dir.exists():
        print(json.dumps({'error': f'书不存在: {args.book}'}, ensure_ascii=False))
        sys.exit(1)

    progress = load_json(book_dir / 'progress.json')
    chapters_meta = load_json(book_dir / 'chapters.json')
    total_book_paragraphs = sum(c['paragraph_count'] for c in chapters_meta)

    # 决定起点
    if args.mode == 'locate':
        chapter_id = args.chapter or 1
        paragraph_idx = args.paragraph or 0
    elif args.mode == 'chapter':
        chapter_id = args.chapter or progress['current_chapter']
        paragraph_idx = 0
    else:  # continue
        chapter_id = progress['current_chapter']
        paragraph_idx = progress['current_paragraph']

    # peek 模式 + offset：模拟"再往后跳 N 批"
    # 用于预合成"下一批"（offset=1）
    if args.peek and args.peek_offset > 0:
        for _ in range(args.peek_offset):
            ch_tmp, paragraphs_tmp = get_chapter_paragraphs(book_dir, chapter_id)
            if ch_tmp is None:
                # 越界：让下面的章节检查报错
                break
            tentative_end = paragraph_idx + args.count
            if tentative_end >= len(paragraphs_tmp):
                # 跨章
                if chapter_id >= len(chapters_meta):
                    # 已到全书末尾，无下一批可预合成
                    print(json.dumps({
                        'is_book_end': True,
                        'message': 'peek beyond book end',
                        'peek_offset': args.peek_offset,
                    }, ensure_ascii=False))
                    return
                chapter_id += 1
                paragraph_idx = 0
            else:
                paragraph_idx = tentative_end

    ch, paragraphs = get_chapter_paragraphs(book_dir, chapter_id)
    if ch is None:
        print(json.dumps({'error': f'章节不存在: {chapter_id}'}, ensure_ascii=False))
        sys.exit(2)

    # 决定取多少段
    if args.mode == 'chapter':
        end_idx = len(paragraphs)
    else:
        end_idx = min(paragraph_idx + args.count, len(paragraphs))

    # 取段
    selected = []
    for i in range(paragraph_idx, end_idx):
        selected.append({
            'index': i,
            'text': paragraphs[i],
            'cache_name': f'ch{chapter_id:03d}_p{i:03d}.wav'
        })

    # 计算下一位置
    is_chapter_end = (end_idx >= len(paragraphs))
    is_book_end = False
    if is_chapter_end:
        if chapter_id >= len(chapters_meta):
            is_book_end = True
            next_chapter = chapter_id
            next_paragraph = len(paragraphs)
        else:
            next_chapter = chapter_id + 1
            next_paragraph = 0
    else:
        next_chapter = chapter_id
        next_paragraph = end_idx

    # 更新进度（peek 模式不更新）
    if not args.peek:
        progress['current_chapter'] = next_chapter
        progress['current_paragraph'] = next_paragraph
        progress['last_read_at'] = datetime.now().isoformat(timespec='seconds')
        progress['total_paragraphs_read'] = progress.get('total_paragraphs_read', 0) + len(selected)
        save_json(book_dir / 'progress.json', progress)

    # 总进度百分比（基于已通读章节段数 + 当前章节段位置）
    paragraphs_before = sum(c['paragraph_count'] for c in chapters_meta[:chapter_id-1])
    cur_position = paragraphs_before + end_idx
    pct = round(cur_position / total_book_paragraphs * 100, 2) if total_book_paragraphs else 0

    print(json.dumps({
        'book': args.book,
        'chapter': chapter_id,
        'chapter_title': ch['title'],
        'chapter_total_paragraphs': len(paragraphs),
        'paragraph_range': [paragraph_idx, end_idx],
        'paragraphs': selected,
        'next_chapter': next_chapter,
        'next_paragraph': next_paragraph,
        'is_chapter_end': is_chapter_end,
        'is_book_end': is_book_end,
        'total_progress_pct': pct,
        'audio_cache_dir': str(book_dir / 'audio_cache'),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
