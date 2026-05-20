#!/usr/bin/env python3
"""
获取并解析华尔街见闻头条新闻。
使用: python3 parse-headlines.py [--limit N]
"""

import argparse
import datetime
import json
import sys
import urllib.request

API_URL = "https://api-one-wscn.awtmt.com/apiv1/content/carousel/information-flow?channel=global&limit={limit}"


def fetch(limit: int = 10) -> dict:
    url = API_URL.format(limit=limit)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_output(data: dict) -> str:
    items = data.get("data", {}).get("items", [])
    lines = []
    lines.append("=" * 44)
    lines.append("  华尔街见闻 · 今日头条")
    lines.append("=" * 44)
    lines.append("")

    for i, item in enumerate(items, 1):
        res = item.get("resource", {})
        title = res.get("title", "")
        summary = res.get("content_short", "")
        author = res.get("author", {}).get("display_name", "")
        uri = res.get("uri", "")
        ts = res.get("display_time", 0)
        time_str = ""
        if ts:
            try:
                time_str = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
            except (ValueError, OSError, OverflowError):
                pass

        lines.append(f"{i}. {title}")
        if summary:
            trunc = summary[:100] + ("..." if len(summary) > 100 else "")
            lines.append(f"   摘要: {trunc}")
        meta = []
        if author:
            meta.append(f"作者: {author}")
        if time_str:
            meta.append(time_str)
        if meta:
            lines.append(f"   {' · '.join(meta)}")
        if uri:
            lines.append(f"   链接: {uri}")
        lines.append("")

    lines.append("=" * 44)
    lines.append(f"共 {len(items)} 条头条")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="获取华尔街见闻头条")
    parser.add_argument("--limit", type=int, default=10, help="返回的头条数量（默认 10）")
    args = parser.parse_args()

    try:
        data = fetch(limit=args.limit)
        print(format_output(data))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
