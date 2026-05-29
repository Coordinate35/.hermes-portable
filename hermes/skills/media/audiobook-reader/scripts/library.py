#!/usr/bin/env python3
"""书库管理：list / info / progress / remove"""
import argparse
import json
import shutil
import sys
from pathlib import Path

EBOOKS_ROOT = Path.home() / 'hermes_data' / 'ebooks'
LIBRARY_FILE = EBOOKS_ROOT / 'library.json'


def load_lib():
    if LIBRARY_FILE.exists():
        return json.loads(LIBRARY_FILE.read_text(encoding='utf-8'))
    return {'books': []}


def cmd_list(args):
    lib = load_lib()
    if not lib['books']:
        print('📚 书库为空')
        return
    print(f'📚 书库共 {len(lib["books"])} 本:')
    for b in lib['books']:
        pg_file = EBOOKS_ROOT / b['title'] / 'progress.json'
        if pg_file.exists():
            pg = json.loads(pg_file.read_text(encoding='utf-8'))
            pg_str = f'第{pg["current_chapter"]}回·段{pg["current_paragraph"]}'
        else:
            pg_str = '未开始'
        print(f'  - {b["title"]} ({b["author"]}) · {b["chapter_count"]}章 · {b["char_count"]:,}字 · 进度: {pg_str}')


def cmd_info(args):
    bd = EBOOKS_ROOT / args.book
    if not bd.exists():
        print(f'❌ 书不存在: {args.book}', file=sys.stderr)
        sys.exit(1)
    meta = json.loads((bd / 'meta.json').read_text(encoding='utf-8'))
    chapters = json.loads((bd / 'chapters.json').read_text(encoding='utf-8'))
    progress = json.loads((bd / 'progress.json').read_text(encoding='utf-8'))
    print(json.dumps({
        'meta': meta,
        'progress': progress,
        'chapters_preview': [{'id': c['id'], 'title': c['title'], 'paragraph_count': c['paragraph_count']} for c in chapters[:5]],
        'total_chapters': len(chapters),
    }, ensure_ascii=False, indent=2))


def cmd_progress(args):
    bd = EBOOKS_ROOT / args.book
    if not bd.exists():
        print(f'❌ 书不存在: {args.book}', file=sys.stderr)
        sys.exit(1)
    progress = json.loads((bd / 'progress.json').read_text(encoding='utf-8'))
    chapters = json.loads((bd / 'chapters.json').read_text(encoding='utf-8'))
    total_para = sum(c['paragraph_count'] for c in chapters)
    paragraphs_before = sum(c['paragraph_count'] for c in chapters[:progress['current_chapter']-1])
    cur = paragraphs_before + progress['current_paragraph']
    pct = round(cur / total_para * 100, 2) if total_para else 0
    ch_title = chapters[progress['current_chapter']-1]['title'] if progress['current_chapter'] <= len(chapters) else '已读完'
    print(json.dumps({
        'book': args.book,
        'current_chapter': progress['current_chapter'],
        'current_chapter_title': ch_title,
        'current_paragraph': progress['current_paragraph'],
        'total_progress_pct': pct,
        'last_read_at': progress['last_read_at'],
        'total_paragraphs_read': progress.get('total_paragraphs_read', 0),
    }, ensure_ascii=False, indent=2))


def cmd_remove(args):
    bd = EBOOKS_ROOT / args.book
    if bd.exists():
        shutil.rmtree(bd)
    lib = load_lib()
    lib['books'] = [b for b in lib['books'] if b['title'] != args.book]
    LIBRARY_FILE.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'✅ 已删除: {args.book}')


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('list')
    for c in ('info', 'progress', 'remove'):
        s = sp.add_parser(c)
        s.add_argument('--book', required=True)
    args = ap.parse_args()
    {'list': cmd_list, 'info': cmd_info, 'progress': cmd_progress, 'remove': cmd_remove}[args.cmd](args)


if __name__ == '__main__':
    main()
