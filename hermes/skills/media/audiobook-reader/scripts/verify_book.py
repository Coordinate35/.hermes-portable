#!/usr/bin/env python3
"""导入后完整性核查脚本。

用法:
  verify_book.py --book "<书名>"
  verify_book.py --book "<书名>" --compare "<另一本书名>"   # 跨版本对比

输出：JSON 报告 + 人类可读摘要到 stderr。
"""
import argparse
import json
import re
import sys
from pathlib import Path

EBOOKS_ROOT = Path.home() / 'hermes_data' / 'ebooks'

# 章节末尾若不以这些字符收尾，疑似被截断
GOOD_TAIL_CHARS = set('。！？”…"\'）)』」.!?）')

# HTML 噪音残留关键词（在章节正文里出现就报警）
NOISE_KEYWORDS = [
    '版权', '本站', '官网', 'Copyright', '免责声明',
    '请记住', '一秒钟', '过目不忘', '推荐顺序',
]


def load_book(title):
    bd = EBOOKS_ROOT / title
    if not bd.exists():
        return None
    meta = json.loads((bd / 'meta.json').read_text(encoding='utf-8'))
    chapters = json.loads((bd / 'chapters.json').read_text(encoding='utf-8'))
    return bd, meta, chapters


def chapter_text(bd, ch):
    return (bd / ch['file']).read_text(encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--compare', help='可选：另一本书名做跨版本对比')
    ap.add_argument('--tail-chars', type=int, default=10, help='末尾抽样字数')
    ap.add_argument('--min-chapter-ratio', type=float, default=0.5,
                    help='章节字数低于平均的此比例视为异常短')
    args = ap.parse_args()

    loaded = load_book(args.book)
    if not loaded:
        print(json.dumps({'error': f'书不存在: {args.book}'}, ensure_ascii=False))
        sys.exit(1)
    bd, meta, chapters = loaded

    report = {
        'book': args.book,
        'meta': {
            'chapter_count': meta['chapter_count'],
            'char_count': meta['char_count'],
            'paragraph_count': meta['paragraph_count'],
        },
        'issues': [],
        'warnings': [],
        'info': [],
    }

    # 1. 汉字数统计
    total_hanzi = 0
    for c in chapters:
        text = chapter_text(bd, c)
        total_hanzi += sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    report['total_hanzi'] = total_hanzi
    report['info'].append(f'汉字数: {total_hanzi:,} (总字符 {meta["char_count"]:,})')

    # 2. 章节字数分布
    char_counts = [c['char_count'] for c in chapters]
    avg = sum(char_counts) / len(char_counts) if char_counts else 0
    threshold = avg * args.min_chapter_ratio
    short_chapters = [(c['id'], c['title'], c['char_count'])
                      for c in chapters if c['char_count'] < threshold]
    report['chapter_stats'] = {
        'min': min(char_counts) if char_counts else 0,
        'max': max(char_counts) if char_counts else 0,
        'avg': round(avg),
        'short_chapters': short_chapters,
    }
    if short_chapters:
        report['warnings'].append(
            f'{len(short_chapters)} 章字数 < 平均 {args.min_chapter_ratio*100:.0f}%, '
            f'需人工确认是否截断或真实差异'
        )

    # 3. 末段完整性
    bad_tails = []
    for c in chapters:
        text = chapter_text(bd, c).rstrip()
        if not text:
            bad_tails.append((c['id'], c['title'], 'EMPTY'))
            continue
        last = text[-1]
        if last not in GOOD_TAIL_CHARS:
            bad_tails.append((c['id'], c['title'], text[-args.tail_chars:]))
    report['bad_tails'] = bad_tails
    if bad_tails:
        report['warnings'].append(
            f'{len(bad_tails)}/{len(chapters)} 章末尾不是完整句标点收尾, '
            f'可能是 HTML 噪音残留（如站方署名）或正文被截断'
        )

    # 4. 重复章节侦测（相邻章标题首 8 字相似 → 报警）
    dup_chapters = []
    for i in range(1, len(chapters)):
        prev_key = re.sub(r'\s+', '', chapters[i-1]['title'])[:8]
        cur_key = re.sub(r'\s+', '', chapters[i]['title'])[:8]
        if prev_key and prev_key == cur_key:
            dup_chapters.append((chapters[i-1]['id'], chapters[i]['id'],
                                 chapters[i]['title']))
    report['dup_chapters'] = dup_chapters
    if dup_chapters:
        report['issues'].append(
            f'{len(dup_chapters)} 处相邻章节标题重复! 可能是 mobi 解析 bug '
            f'(同章被切两次)。详情: {dup_chapters}'
        )

    # 5. HTML 噪音残留
    noise_hits = []
    for c in chapters:
        text = chapter_text(bd, c)
        tail = text[-200:]  # 噪音通常在末尾
        for kw in NOISE_KEYWORDS:
            if kw in tail:
                noise_hits.append((c['id'], c['title'], kw))
                break
    report['noise_hits'] = noise_hits
    if noise_hits:
        report['warnings'].append(
            f'{len(noise_hits)} 章末尾含 HTML 噪音关键词, '
            f'考虑在 crawler 阶段加 skip_keywords 或导入后批量清洗'
        )

    # 6. 跨版本对比
    if args.compare:
        other = load_book(args.compare)
        if other:
            obd, ometa, ochapters = other
            report['compare_with'] = args.compare
            big_diffs = []
            for i in range(min(len(chapters), len(ochapters))):
                a = chapters[i]['char_count']
                b = ochapters[i]['char_count']
                if a == 0:
                    continue
                pct = (b - a) / a * 100
                if abs(pct) > 30:
                    big_diffs.append({
                        'chapter': i + 1,
                        'this': a, 'other': b,
                        'diff_pct': round(pct, 1),
                        'this_title': chapters[i]['title'],
                        'other_title': ochapters[i]['title'],
                    })
            report['big_diff_chapters'] = big_diffs
            if big_diffs:
                report['warnings'].append(
                    f'{len(big_diffs)} 回与对比版字数差 > 30%, '
                    f'可能是真实版本差异或数据缺失，需逐回确认'
                )

    # 输出
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 人类可读摘要到 stderr
    sym_issue = '❌' if report['issues'] else '✅'
    sym_warn = '⚠️ ' if report['warnings'] else '✅'
    print(f'\n{sym_issue} 严重问题: {len(report["issues"])}', file=sys.stderr)
    for i in report['issues']:
        print(f'   - {i}', file=sys.stderr)
    print(f'{sym_warn} 警告: {len(report["warnings"])}', file=sys.stderr)
    for w in report['warnings']:
        print(f'   - {w}', file=sys.stderr)


if __name__ == '__main__':
    main()
