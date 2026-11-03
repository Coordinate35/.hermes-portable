#!/usr/bin/env python3
"""下载单条微博（含转发对象）的配图，供推送时以 MEDIA: 附件发出。

用法:
    PYTHONPATH= /usr/bin/python3 wb_download_pics.py <weibo_id> [--dir DIR]

输出: 一行 JSON —— {"id":..., "files":[...], "count":N, "sources":[...]}
落盘: 默认 ~/hermes_data/weibo_data/images/<weibo_id>/
"""
import sys
import os
import json
import argparse

import requests

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
IMG_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = os.path.expanduser("~/hermes_data/weibo_data/articles/images")


def pics(mb):
    out = []
    for p in (mb or {}).get("pics", []) or []:
        url = (p.get("large") or {}).get("url") or p.get("url")
        if url:
            out.append(url)
    return out


def upgrade(url):
    """mw2000 -> large（原图）；失败时下载端会回退。"""
    return url.replace("/mw2000/", "/large/")


def download(url, dest):
    for cand in (upgrade(url), url):
        try:
            r = requests.get(cand, headers={"User-Agent": IMG_UA, "Referer": "https://weibo.com/"},
                             timeout=30)
            if r.status_code == 200 and len(r.content) > 1024:
                with open(dest, "wb") as f:
                    f.write(r.content)
                return len(r.content), cand
        except Exception:
            continue
    return 0, url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("weibo_id")
    ap.add_argument("--dir", default=None)
    a = ap.parse_args()

    r = requests.get("https://m.weibo.cn/statuses/show",
                     params={"id": a.weibo_id},
                     headers={"User-Agent": UA,
                              "X-Requested-With": "XMLHttpRequest",
                              "Referer": f"https://m.weibo.cn/detail/{a.weibo_id}"},
                     timeout=20)
    data = (r.json() or {}).get("data") or {}

    pairs = [(u, "本条") for u in pics(data)]
    pairs += [(u, "转发对象") for u in pics(data.get("retweeted_status"))]

    outdir = a.dir or os.path.join(BASE, str(a.weibo_id))
    os.makedirs(outdir, exist_ok=True)

    files, meta = [], []
    for i, (u, src) in enumerate(pairs, 1):
        ext = os.path.splitext(u.split("?")[0])[1] or ".jpg"
        dest = os.path.join(outdir, f"{i:02d}{ext}")
        size, used = download(u, dest)
        if size:
            files.append(dest)
            meta.append({"file": dest, "bytes": size, "url": used, "from": src})
        else:
            meta.append({"file": None, "bytes": 0, "url": u, "from": src})

    print(json.dumps({"id": a.weibo_id, "count": len(files), "files": files, "detail": meta},
                     ensure_ascii=False))
    return 0 if files else 1


if __name__ == "__main__":
    sys.exit(main())
