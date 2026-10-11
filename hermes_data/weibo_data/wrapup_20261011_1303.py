#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本批收尾（2026-10-11 13:03 批）：两条评论配图链接三形式缓存回写＋compic 页可达复核。"""
import json
import subprocess

import requests

LC = "/home/coordinate35/.hermes/skills/data-collection/weibo-monitoring/scripts/link_cache.py"


def store(payload):
    r = subprocess.run(["python3", LC, "store", "-"],
                       input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True)
    out = (r.stdout or "").strip().replace("\n", " ")
    err = (r.stderr or "").strip().replace("\n", " ")
    print("store rc:", r.returncode, "|", out[:200], ("| ERR: " + err[:200]) if err else "")


A = {
    "url": "https://photo.weibo.com/h5/comment/compic_id/1022:230597cf7a1c56523cc88033e101c0c572f13b",
    "kind": "weibo_compic",
    "title": "评论配图页（@用户6282460088 评论附图；原帖 5352468893666628）",
    "extra": "t.cn 302 直达；源帖 5352468893666628",
}
store({**A, "sinaurl": "http://t.cn/AXlb8wUt"})
store({**A, "sinaurl": "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx3.sinaimg.cn%2Flarge%2F006RayRqgy1ihx6vhvetej30v4177wmo.jpg"})
store({**A, "sinaurl": "https://wx3.sinaimg.cn/large/006RayRqgy1ihx6vhvetej30v4177wmo.jpg"})

B = {
    "url": "https://photo.weibo.com/h5/comment/compic_id/1022:230597d935396ca01760d8d5422f8f0a4131aa",
    "kind": "weibo_compic",
    "title": "评论配图页（@兔兔归来V 评论附图；原帖 5352808568326193）",
    "extra": "t.cn 302 直达；源帖 5352808568326193",
}
store({**B, "sinaurl": "http://t.cn/AXltruhY"})
store({**B, "sinaurl": "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx4.sinaimg.cn%2Flarge%2F008qcccYgy1ihyaducp5jj310o1hxqgq.jpg"})
store({**B, "sinaurl": "https://wx4.sinaimg.cn/large/008qcccYgy1ihyaducp5jj310o1hxqgq.jpg"})

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")
for u in (A["url"], B["url"]):
    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=20)
        print("compic recheck:", r.status_code, len(r.content), "| imgs:", r.text.count("<img"))
    except Exception as e:
        print("compic recheck ERR:", repr(e))

r = subprocess.run(["python3", LC, "check",
                    "http://t.cn/AXlb8wUt",
                    "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx3.sinaimg.cn%2Flarge%2F006RayRqgy1ihx6vhvetej30v4177wmo.jpg",
                    "https://wx3.sinaimg.cn/large/006RayRqgy1ihx6vhvetej30v4177wmo.jpg",
                    "http://t.cn/AXltruhY",
                    "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx4.sinaimg.cn%2Flarge%2F008qcccYgy1ihyaducp5jj310o1hxqgq.jpg",
                    "https://wx4.sinaimg.cn/large/008qcccYgy1ihyaducp5jj310o1hxqgq.jpg"],
                   capture_output=True, text=True)
print("check rc:", r.returncode)
for line in (r.stdout or "").splitlines():
    print(" ", line[:160])
