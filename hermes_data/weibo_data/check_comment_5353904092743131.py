#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核验@邹江的微博 留言落点：搜 5353643676534669（及其近邻帖）评论，找到含『报报平安』的评论"""
import sys, os, json
import requests

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w  # noqa: E402

def fetch_comments(pid):
    url = f"https://m.weibo.cn/comments/hotflow?id={pid}&mid={pid}&max_id_type=0"
    r = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=25)
    try:
        return r.json()
    except Exception:
        return {"__raw": r.text[:500]}

def walk(data, hits, path=""):
    if isinstance(data, dict):
        for k, v in data.items():
            walk(v, hits, path + "/" + str(k))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            walk(v, hits, path + f"[{i}]")
    elif isinstance(data, str):
        if "报报平安" in data or "邹江" in data:
            hits.append((path, data[:300]))

for pid in ["5353643676534669"]:
    d = fetch_comments(pid)
    ok = d.get("ok")
    print(f"== post {pid} ok={ok} ==")
    hits = []
    walk(d, hits)
    print("hits:", len(hits))
    for p, s in hits[:20]:
        print(p, "=>", s)
    # 也看第一条评论的用户名列表
    datas = d.get("data", {}).get("data", []) if isinstance(d.get("data"), dict) else []
    if isinstance(datas, list):
        print("comment count in page:", len(datas))
        for c in datas[:15]:
            u = c.get("user", {}).get("screen_name")
            t = c.get("text", "")
            import re as _re
            t2 = _re.sub(r"<[^>]+>", "", t)
            print("-", u, "|", t2[:80])
