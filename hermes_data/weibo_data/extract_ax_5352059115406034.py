#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only: extract analysis_extra / mblog_rt_mid / mblog_parent_id from m.weibo.cn render page."""
import os
import re
import sys

import requests

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w  # noqa: E402

mid = sys.argv[1] if len(sys.argv) > 1 else "5352059115406034"
url = f"https://m.weibo.cn/status/{mid}?_=2"
r = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=25, allow_redirects=True)
txt = r.text
print(f"status={r.status_code} len={len(txt)} visitor_wall={'Sina Visitor System' in txt}")

for key in ("mblog_rt_mid", "mblog_parent_id"):
    vals = re.findall(re.escape(key) + r"[\"':=]+(\d{10,20})", txt)
    print(f"{key}: {sorted(set(vals))}")

i = txt.find("analysis_extra")
print("analysis_extra first idx:", i)
if i >= 0:
    seg = txt[max(0, i - 60):i + 500]
    print("RAW:", seg.replace("\n", "\\n"))
    try:
        dec = seg.encode("utf-8").decode("unicode_escape")
        print("DECODED:", dec.replace("\n", "\\n")[:600])
    except Exception as e:  # noqa: BLE001
        print("decode err:", e)
