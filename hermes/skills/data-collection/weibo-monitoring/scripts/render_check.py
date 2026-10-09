#!/usr/bin/env python3
"""Fetch m.weibo.cn render page(s) for an id (read-only) to cross-verify the displayed
text cutoff / absence of deeper expandable content.

Usage:
    cd ~/.hermes/scripts && PYTHONPATH=. python3 <this_script> <id> [marker ...]

For each render URL prints JSON: status / final_url / len / visitor_wall flag,
counts of 展开全文/查看全文/查看更多/全文, and marker occurrence contexts.
"""
import sys
import os
import json

import requests

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: render_check.py <id> [marker ...]", file=sys.stderr)
        return 2
    mid = sys.argv[1]
    markers = sys.argv[2:] or ["全球穿透式交易的有效", "请新浪不要乱删"]

    targets = [
        f"https://m.weibo.cn/status/{mid}?_=2",
        f"https://m.weibo.cn/detail/{mid}?_=2",
    ]
    for url in targets:
        try:
            r = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES,
                             timeout=25, allow_redirects=True)
            txt = r.text
            info = {
                "url": url,
                "status": r.status_code,
                "final_url": str(r.url),
                "len": len(txt),
                "visitor_wall": ("Sina Visitor System" in txt
                                 or "visitor.passport" in str(r.url)),
            }
            for kw in ["展开全文", "查看全文", "查看更多", "全文"]:
                info[f"count_{kw}"] = txt.count(kw)
            for m in markers:
                cs = []
                start = 0
                while True:
                    i = txt.find(m, start)
                    if i < 0:
                        break
                    cs.append(i)
                    start = i + 1
                ctxs = []
                for i in cs[:6]:
                    snippet = txt[max(0, i - 70):i + len(m) + 70]
                    ctxs.append(snippet.replace("\n", "\\n"))
                info[f"occ[{m}]"] = len(cs)
                info[f"ctx[{m}]"] = ctxs
            print(json.dumps(info, ensure_ascii=False)[:4500])
            print("---")
        except Exception as e:
            print(json.dumps({"url": url, "error": str(e)}, ensure_ascii=False))
            print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
