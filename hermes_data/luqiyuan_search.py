#!/usr/bin/env python3
"""
卢麒元投资学原文检索系统
支持: 关键词搜索、多关键词搜索、按文档过滤、上下文预览
使用: python3 luqiyuan_search.py "真实通胀" --limit 5
"""
import json
import sys
import re
import argparse
from pathlib import Path

JSONL_PATH = "/home/coordinate35/hermes_data/luqiyuan_chunks.jsonl"

def load_chunks():
    chunks = []
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line.strip()))
    return chunks

def search_chunks(chunks, query, doc_filter=None, limit=10, context_chars=100):
    """
    简单关键词搜索: 支持多个关键词（空格分隔），所有关键词都必须出现
    """
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    
    results = []
    for chunk in chunks:
        if doc_filter and chunk.get('doc', chunk.get('doc_name', '')) not in doc_filter:
            continue
        text = chunk['text']
        match = True
        matched_positions = []
        for kw in keywords:
            pos = text.find(kw)
            if pos == -1:
                match = False
                break
            matched_positions.append(pos)
        if match:
            # 生成上下文预览
            if matched_positions:
                center = min(matched_positions)
                start = max(0, center - context_chars)
                end = min(len(text), center + context_chars)
                preview = text[start:end]
                if start > 0:
                    preview = '...' + preview
                if end < len(text):
                    preview = preview + '...'
            else:
                preview = text[:200]
            
            # 高亮关键词
            for kw in keywords:
                preview = preview.replace(kw, f'\033[91m{kw}\033[0m')
            
            results.append({
                'doc_name': chunk.get('doc', chunk.get('doc_name', '')),
                'chunk_id': chunk['chunk_id'],
                'start': chunk['start'],
                'end': chunk['end'],
                'preview': preview,
                'text': text
            })
    
    return results[:limit]

def main():
    parser = argparse.ArgumentParser(description='卢麒元投资学原文检索')
    parser.add_argument('query', help='搜索关键词，多个词用空格分隔')
    parser.add_argument('--doc', help='指定文档名（如"投资学2019"）')
    parser.add_argument('--limit', type=int, default=10, help='返回结果数量')
    parser.add_argument('--context', type=int, default=150, help='预览上下文字符数')
    parser.add_argument('--full', action='store_true', help='显示完整不是预览')
    args = parser.parse_args()
    
    print(f"正在加载索引...", file=sys.stderr)
    chunks = load_chunks()
    print(f"已加载 {len(chunks)} 个文本块", file=sys.stderr)
    
    doc_filter = [args.doc] if args.doc else None
    results = search_chunks(chunks, args.query, doc_filter, args.limit, args.context)
    
    if not results:
        print("未找到匹配结果")
        return
    
    print(f"\n找到 {len(results)} 个匹配结果:\n")
    for i, r in enumerate(results, 1):
        print(f"{'='*80}")
        print(f"[{i}] 文档: {r['doc_name']} | 块{r['chunk_id']} | 位置:{r['start']}-{r['end']}")
        print(f"{'-'*80}")
        if args.full:
            print(r['text'])
        else:
            print(r['preview'])
        print()

if __name__ == '__main__':
    main()
