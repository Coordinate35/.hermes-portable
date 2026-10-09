#!/usr/bin/env python3
"""本批收尾（2026-10-09 21:35 批）：评论配图链接缓存回写（t.cn/ sinaurl/ 解码 三形式）＋ compic 页可达复核。"""
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
    print("store rc:", r.returncode, "|", out[:300], ("| ERR: " + err[:200]) if err else "")


BASE = {
    "url": "https://photo.weibo.com/h5/comment/compic_id/1022:2329755352220973599151",
    "kind": "weibo_compic",
    "title": "评论配图页（@中庸之道常驻于心w_b25- 评论附图，共2张）",
    "extra": "t.cn 302 直达；源帖 5352222980312578",
}
store({**BASE, "sinaurl": "http://t.cn/AXlUveQJ"})
store({**BASE, "sinaurl": "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx3.sinaimg.cn%2Flarge%2F0063WZjhgy1ihwf5iqgabj30wi1yc1kx.jpg"})
store({**BASE, "sinaurl": "https://wx3.sinaimg.cn/large/0063WZjhgy1ihwf5iqgabj30wi1yc1kx.jpg"})

# compic 页可达复核
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")
u = "https://photo.weibo.com/h5/comment/compic_id/1022:2329755352220973599151"
try:
    r = requests.get(u, headers={"User-Agent": UA}, timeout=20)
    print("compic recheck:", r.status_code, len(r.content), "| 共2张:", ("共2张图片" in r.text))
except Exception as e:
    print("compic recheck ERR:", repr(e))

# 缓存回读验证（三形式均须 HIT）
r = subprocess.run(["python3", LC, "check",
                    "http://t.cn/AXlUveQJ",
                    "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx3.sinaimg.cn%2Flarge%2F0063WZjhgy1ihwf5iqgabj30wi1yc1kx.jpg",
                    "https://wx3.sinaimg.cn/large/0063WZjhgy1ihwf5iqgabj30wi1yc1kx.jpg"],
                   capture_output=True, text=True)
print("check rc:", r.returncode)
for line in (r.stdout or "").splitlines():
    print(" ", line[:200])
