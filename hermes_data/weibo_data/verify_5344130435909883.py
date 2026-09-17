#!/usr/bin/env python3
"""核验 5344130435909883 的权威完整文本（show / pc-longtext / m 渲染 三源）。"""
import sys, re, json
sys.path.insert(0, "/home/coordinate35/.hermes/scripts")
import requests
import weibo_monitor as w

WID = "5344130435909883"

print("=" * 30, "SOURCE 1: m.weibo.cn show API", "=" * 30)
try:
    r = requests.get(
        f"https://m.weibo.cn/statuses/show?id={WID}",
        headers={**w.HEADERS, "X-Requested-With": "XMLHttpRequest",
                 "Referer": f"https://m.weibo.cn/detail/{WID}"},
        cookies=w.COOKIES, timeout=15,
    )
    d = r.json().get("data", {})
    for k in ("text", "raw_text", "longTextContent"):
        v = d.get(k)
        if v:
            v2 = re.sub(r"<[^>]+>", "", v)
            print(f"--- {k} (len={len(v2)}) ---")
            print(v2)
    print(f"--- isLongText={d.get('isLongText')} ---")
except Exception as e:
    print("SHOW FAILED:", e)

print()
print("=" * 30, "SOURCE 2: weibo.com ajax longtext", "=" * 30)
try:
    r = requests.get(
        f"https://weibo.com/ajax/statuses/longtext?id={WID}",
        headers={**w.HEADERS, "Referer": "https://weibo.com/"},
        cookies=w.COOKIES, timeout=15,
    )
    d = r.json().get("data", {})
    v = d.get("longTextContent") or ""
    v2 = re.sub(r"<[^>]+>", "", v)
    print(f"--- longTextContent (len={len(v2)}) ---")
    print(v2)
except Exception as e:
    print("LONGTEXT FAILED:", e)

print()
print("=" * 30, "SOURCE 3: m.weibo.cn render ?_=2", "=" * 30)
try:
    r = requests.get(
        f"https://m.weibo.cn/status/{WID}?_=2",
        headers=w.HEADERS, cookies=w.COOKIES, timeout=20,
    )
    html = r.text
    print("expand markers 展开全文 count:", html.count("展开全文"))
    for m in re.finditer("理应让人民分享国家发展的", html):
        s = max(0, m.start() - 40); e = min(len(html), m.end() + 80)
        print("CTX:", html[s:e].replace("\n", "\\n"))
    for kw in ("斗兽场", "匪夷所思", "金殖"):
        print(f"kw {kw}: {html.count(kw)} occurrences")
    # 检查渲染里该链尾之后是否有更深内容副本
    idx = html.rfind("理应让人民分享国家发展的")
    if idx != -1:
        print("TAIL after last occurrence:", html[idx:idx+300].replace("\n", "\\n"))
except Exception as e:
    print("RENDER FAILED:", e)
