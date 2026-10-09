#!/usr/bin/env python3
"""Dump m.weibo.cn show-endpoint data for one mblog id (authoritative raw_text + key fields).

Usage:
    cd ~/.hermes/scripts && PYTHONPATH=. python3 \
      ~/.hermes/skills/data-collection/weibo-monitoring/scripts/wb_show_dump.py <mblog_id>

Outputs JSON to stdout; also saves full JSON to ~/hermes_data/weibo_data/wb_verify_<id>.json
Fields: raw_text (authoritative, emoji-preserving), text_stripped, hrefs, repost_type,
isLongText, long_text (extend), pc_longtext (weibo.com ajax), retweeted_status (if any).
"""
import sys
import os
import json
import re

import requests

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w  # noqa: E402  (reuse HEADERS / COOKIES)


def strip_html(t: str) -> str:
    return re.sub(r"<[^>]+>", "", t or "")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: wb_show_dump.py <mblog_id>", file=sys.stderr)
        return 2
    mid = sys.argv[1]

    hdrs = dict(w.HEADERS)
    hdrs.update({
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://m.weibo.cn/detail/{mid}",
    })

    try:
        r = requests.get(
            f"https://m.weibo.cn/statuses/show?id={mid}",
            headers=hdrs, cookies=w.COOKIES, timeout=20,
        )
        j = r.json()
    except Exception as e:
        print(json.dumps({"error": f"show request failed: {e}"}, ensure_ascii=False))
        return 1

    if j.get("ok") != 1:
        print(json.dumps({"error": "show ok!=1", "resp": str(j)[:600]}, ensure_ascii=False))
        return 1

    data = j.get("data") or {}
    out = {
        "id": str(data.get("id")),
        "created_at": data.get("created_at"),
        "source": data.get("source"),
        "repost_type": data.get("repost_type"),
        "isLongText": data.get("isLongText"),
        "raw_text": data.get("raw_text"),
        "text_stripped": strip_html(data.get("text", "")),
        "hrefs": re.findall(r'href="([^"]+)"', data.get("text", "") or ""),
        "pic_num": data.get("pic_num"),
        "comments_count": data.get("comments_count"),
        "reposts_count": data.get("reposts_count"),
        "attitudes_count": data.get("attitudes_count"),
    }

    if data.get("isLongText"):
        try:
            r3 = requests.get(
                f"https://m.weibo.cn/statuses/extend?id={mid}",
                headers=w.HEADERS, cookies=w.COOKIES, timeout=20,
            ).json()
            out["long_text"] = strip_html(r3.get("data", {}).get("longTextContent", ""))
        except Exception as e:
            out["long_text"] = f"[extend failed: {e}]"

    try:
        r4 = requests.get(
            f"https://weibo.com/ajax/statuses/longtext?id={mid}",
            headers=dict(w.HEADERS, Referer=f"https://weibo.com/detail/{mid}"),
            cookies=w.COOKIES, timeout=20,
        ).json()
        out["pc_longtext"] = strip_html((r4.get("data") or {}).get("longTextContent", ""))
    except Exception as e:
        out["pc_longtext"] = f"[pc longtext failed: {e}]"

    rs = data.get("retweeted_status")
    if rs:
        rs_out = {
            "id": str(rs.get("id")),
            "user": (rs.get("user") or {}).get("screen_name"),
            "created_at": rs.get("created_at"),
            "isLongText": rs.get("isLongText"),
            "raw_text": rs.get("raw_text"),
            "text_stripped": strip_html(rs.get("text", "")),
            "pic_num": rs.get("pic_num"),
        }
        if rs.get("isLongText"):
            try:
                r5 = requests.get(
                    f"https://m.weibo.cn/statuses/extend?id={rs.get('id')}",
                    headers=w.HEADERS, cookies=w.COOKIES, timeout=20,
                ).json()
                rs_out["long_text"] = strip_html(r5.get("data", {}).get("longTextContent", ""))
            except Exception as e:
                rs_out["long_text"] = f"[extend failed: {e}]"
        out["retweeted_status"] = rs_out

    savep = os.path.expanduser(f"~/hermes_data/weibo_data/wb_verify_{mid}.json")
    os.makedirs(os.path.dirname(savep), exist_ok=True)
    with open(savep, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\nSAVED: {savep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
