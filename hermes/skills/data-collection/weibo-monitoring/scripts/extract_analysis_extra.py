#!/usr/bin/env python3
"""Extract analysis_extra (mblog_rt_mid / mblog_parent_id) from the m.weibo.cn render
page of a post — chain-structure judgment for reply / self-chain posts.

Usage:
    cd ~/.hermes/skills/data-collection/weibo-monitoring/scripts && \
      PYTHONPATH= /usr/bin/python3 extract_analysis_extra.py <id>

Interpretation: mblog_rt_mid = 帖内转发卡片 id; mblog_parent_id = 评论所在帖 id.
"""
import sys
import os
import re

import requests

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: extract_analysis_extra.py <id>", file=sys.stderr)
        return 2
    mid = sys.argv[1]
    url = f"https://m.weibo.cn/status/{mid}?_=2"
    r = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES,
                     timeout=25, allow_redirects=True)
    txt = r.text
    print("status:", r.status_code, "len:", len(txt),
          "wall:", ("Sina Visitor System" in txt or "visitor.passport" in str(r.url)))
    seen = set()
    for pat in [r"analysis_extra[^\n]{0,400}", r"mblog_rt_mid:\d+", r"mblog_parent_id:\d+"]:
        for m in re.finditer(pat, txt):
            s = m.group(0)
            if s in seen:
                continue
            seen.add(s)
            print(">>", s[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
