#!/usr/bin/env python3
"""
解析单条微博 show 接口，提取正文 HTML 中的外部链接（sinaurl → 外站 URL）。
用于"外部链接分享型"微博（正文为标题短句＋`网页链接` 占位、article_url 为空）:
真实链接藏在 show 接口 data.text 的 <a href>（weibo.cn/sinaurl?u=<URL编码>）里。

用法:
    cd ~/.hermes/scripts && PYTHONPATH=. python3 <this_script> <weibo_id>
依赖: weibo_monitor.py 必须在 PYTHONPATH 中（复用 HEADERS / COOKIES）
输出: HTTP 状态、正文 HTML、raw_text、page_info、全部 hrefs、sinaurl 解码结果
"""
import sys
import json
import re
from urllib.parse import unquote

import requests
import weibo_monitor as w

wid = sys.argv[1]
r = requests.get(
    f"https://m.weibo.cn/statuses/show?id={wid}",
    headers={
        **w.HEADERS,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://m.weibo.cn/detail/{wid}",
    },
    cookies=w.COOKIES,
    timeout=15,
)
print("HTTP:", r.status_code)
data = (r.json() or {}).get("data", {}) or {}
text_html = data.get("text", "") or ""
print("TEXT_HTML:", text_html)
print("RAW_TEXT:", (data.get("raw_text", "") or "")[:500])
pi = data.get("page_info") or {}
print(
    "PAGE_INFO:",
    json.dumps(
        {k: pi.get(k) for k in ("type", "title", "page_url", "url_ori")},
        ensure_ascii=False,
    ),
)
hrefs = re.findall(r'href="([^"]+)"', text_html)
print("HREFS:", json.dumps(hrefs, ensure_ascii=False))
for h in hrefs:
    m = re.search(r"[?&]u=([^&]+)", h)
    if m:
        print("DECODED:", unquote(m.group(1)))
