#!/usr/bin/env python3
"""
拉取单条微博的完整 mblog 对象（含 retweeted_status / 长文全文 / 配图）。

用法:
    cd ~/.hermes/scripts && PYTHONPATH=. python3 <this_script> <uid> <weibo_id>

输出: 一行 JSON，字段见同目录 references/retweet-and-longtext-extraction.md
依赖: weibo_monitor.py 必须在 PYTHONPATH 中（用它的 HEADERS / COOKIES）
"""
import sys
import json
import re

import requests
import weibo_monitor as w  # 复用 cookie / headers


def strip_html(t: str) -> str:
    return re.sub(r"<[^>]+>", "", t or "")


def fetch_long(mid: str) -> str:
    try:
        r = requests.get(
            f"https://m.weibo.cn/statuses/extend?id={mid}",
            headers=w.HEADERS,
            cookies=w.COOKIES,
            timeout=15,
        ).json()
        return strip_html(r.get("data", {}).get("longTextContent", ""))
    except Exception as e:
        return f"[long fetch failed: {e}]"


def pic_urls(mb: dict) -> list:
    out = []
    for p in mb.get("pics", []) or []:
        url = (p.get("large") or {}).get("url") or p.get("url")
        if url:
            out.append(url)
    return out


def shrink_retweet(rs: dict) -> dict:
    out = {
        "user": (rs.get("user") or {}).get("screen_name"),
        "text": strip_html(rs.get("text", "")),
        "is_long_text": bool(rs.get("isLongText")),
        "pic_urls": pic_urls(rs),
    }
    if out["is_long_text"]:
        out["long_text"] = fetch_long(rs.get("id"))
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: fetch_mblog_full.py <uid> <weibo_id>", file=sys.stderr)
        return 2
    uid, wid = sys.argv[1], sys.argv[2]
    url = (
        f"https://m.weibo.cn/api/container/getIndex"
        f"?uid={uid}&type=uid&value={uid}&containerid=107603{uid}"
    )
    data = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=15).json()
    for c in data.get("data", {}).get("cards", []):
        if c.get("card_type") != 9:
            continue
        mb = c.get("mblog") or {}
        if str(mb.get("id")) != str(wid):
            continue
        out = {
            "id": mb.get("id"),
            "bid": mb.get("bid"),
            "text": strip_html(mb.get("text", "")),
            "raw_text": mb.get("raw_text", ""),
            "is_long_text": bool(mb.get("isLongText")),
            "pic_urls": pic_urls(mb),
        }
        if out["is_long_text"]:
            out["long_text"] = fetch_long(mb.get("id"))
        if mb.get("retweeted_status"):
            out["retweet"] = shrink_retweet(mb["retweeted_status"])
        print(json.dumps(out, ensure_ascii=False))
        return 0
    print(json.dumps({"error": "not_found_in_timeline_window"}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
