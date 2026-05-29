#!/usr/bin/env python3
"""导入一本书到书库：解析 → 切章 → 建索引 → 写元数据。

用法:
  add_book.py --source <file_path_or_url> --title "射雕英雄传" [--author "金庸"] [--version "三联修订版"]
"""
import argparse
import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# 让 parsers 可导入
sys.path.insert(0, str(Path(__file__).parent))
from parsers import parse_book, split_into_paragraphs

EBOOKS_ROOT = Path.home() / 'hermes_data' / 'ebooks'
LIBRARY_FILE = EBOOKS_ROOT / 'library.json'


def load_library():
    if LIBRARY_FILE.exists():
        return json.loads(LIBRARY_FILE.read_text(encoding='utf-8'))
    return {'books': []}


def save_library(lib):
    LIBRARY_FILE.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding='utf-8')


def fetch_source(source: str, dest_dir: Path) -> Path:
    """把 source 落到 dest_dir/source.<ext>。返回最终路径。"""
    if source.startswith(('http://', 'https://')):
        # 推断扩展名
        ext = os.path.splitext(source.split('?')[0])[1].lstrip('.').lower() or 'epub'
        dest = dest_dir / f'source.{ext}'
        print(f'[下载] {source} → {dest}', file=sys.stderr)
        req = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
            shutil.copyfileobj(r, f)
        return dest
    src = Path(source).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")
    ext = src.suffix.lstrip('.').lower()
    dest = dest_dir / f'source.{ext}'
    shutil.copy2(src, dest)
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='本地路径或URL')
    ap.add_argument('--title', required=True, help='书名（用作目录名）')
    ap.add_argument('--author', default='', help='作者')
    ap.add_argument('--version', default='', help='版本说明')
    ap.add_argument('--force', action='store_true', help='覆盖已存在的同名书')
    args = ap.parse_args()

    book_dir = EBOOKS_ROOT / args.title
    if book_dir.exists() and not args.force:
        print(f'❌ 书已存在: {book_dir}（用 --force 覆盖）', file=sys.stderr)
        sys.exit(1)

    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / 'chapters').mkdir(exist_ok=True)
    (book_dir / 'audio_cache').mkdir(exist_ok=True)

    # 1. 获取源文件
    src_path = fetch_source(args.source, book_dir)
    print(f'[就绪] 源文件: {src_path} ({src_path.stat().st_size} bytes)', file=sys.stderr)

    # 2. 解析
    chapters = parse_book(str(src_path))
    if not chapters:
        print('❌ 解析失败，未提取到任何章节', file=sys.stderr)
        sys.exit(2)

    # 3. 切段 + 写章节
    chapter_index = []
    total_chars = 0
    total_paragraphs = 0
    for i, ch in enumerate(chapters, 1):
        paragraphs = split_into_paragraphs(ch['text'])
        if not paragraphs:
            continue
        ch_id = f'{i:03d}'
        ch_path = book_dir / 'chapters' / f'{ch_id}.txt'
        # 用 \n\n 分隔段落，方便后续按段读取
        ch_path.write_text('\n\n'.join(paragraphs), encoding='utf-8')
        char_count = sum(len(p) for p in paragraphs)
        chapter_index.append({
            'id': i,
            'title': ch['title'],
            'paragraph_count': len(paragraphs),
            'char_count': char_count,
            'file': f'chapters/{ch_id}.txt'
        })
        total_chars += char_count
        total_paragraphs += len(paragraphs)

    # 4. 写 chapters.json
    (book_dir / 'chapters.json').write_text(
        json.dumps(chapter_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 5. 写 meta.json
    meta = {
        'title': args.title,
        'author': args.author,
        'version': args.version,
        'source_file': src_path.name,
        'source_format': src_path.suffix.lstrip('.'),
        'imported_at': datetime.now().isoformat(timespec='seconds'),
        'chapter_count': len(chapter_index),
        'paragraph_count': total_paragraphs,
        'char_count': total_chars,
    }
    (book_dir / 'meta.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    # 6. 初始化 progress.json（如果不存在）
    progress_path = book_dir / 'progress.json'
    if not progress_path.exists():
        progress_path.write_text(json.dumps({
            'current_chapter': 1,
            'current_paragraph': 0,
            'last_read_at': None,
            'total_paragraphs_read': 0
        }, ensure_ascii=False, indent=2), encoding='utf-8')

    # 7. 更新 library.json
    lib = load_library()
    lib['books'] = [b for b in lib['books'] if b['title'] != args.title]
    lib['books'].append({
        'title': args.title,
        'author': args.author,
        'version': args.version,
        'chapter_count': len(chapter_index),
        'char_count': total_chars,
        'imported_at': meta['imported_at'],
    })
    save_library(lib)

    print(json.dumps({
        'status': 'ok',
        'title': args.title,
        'chapter_count': len(chapter_index),
        'paragraph_count': total_paragraphs,
        'char_count': total_chars,
        'book_dir': str(book_dir),
        'first_3_chapters': [c['title'] for c in chapter_index[:3]],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
