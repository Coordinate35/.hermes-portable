#!/usr/bin/env python3
"""
链接解析缓存（2026-09-28）：已解析过的外链只解析一次。

存档：~/hermes_data/weibo_data/link_cache.json（与 last_weibo.json 同目录）
用法:
    python3 link_cache.py check '<url1>' ['<url2>' ...]   # 逐条输出 HIT/MISS
    python3 link_cache.py store '<单行JSON>'               # 写入/更新一条记录（'-' 表示从 stdin 读）

check 输入可为外站 URL / sinaurl / t.cn 短链（归一化后匹配 url 或 sinaurl 别名）。
store JSON 字段: url(必填), sinaurl, kind, title, author, date, extra(自由文本)
"""
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

CACHE_PATH = os.path.expanduser("~/hermes_data/weibo_data/link_cache.json")
_FIELDS = ("title", "author", "date", "kind", "extra")


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _norm(url: str) -> str:
    """归一化：scheme/host 小写、去尾斜杠、去 fragment、保留 query。"""
    u = (url or "").strip()
    if not u:
        return ""
    p = urlsplit(u)
    return urlunsplit(
        ((p.scheme or "https").lower(), p.netloc.lower(), p.path.rstrip("/"), p.query, "")
    )


def _load() -> dict:
    empty = {"version": 1, "links": {}, "aliases": {}}
    if not os.path.exists(CACHE_PATH):
        return empty
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or not isinstance(d.get("links"), dict):
            raise ValueError("bad structure")
        d.setdefault("aliases", {})
        return d
    except Exception as e:
        sys.stderr.write(f"link_cache: WARN 缓存读取失败({e})，本次按空缓存运行\n")
        return empty


def _save(d: dict) -> None:
    """原子写：tmp + os.replace，避免半写损坏。"""
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    tmp = f"{CACHE_PATH}.tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CACHE_PATH)


def lookup(url: str):
    """查一条（命中时累计 hits/last_seen_at 并落盘）；返回记录 dict 或 None。"""
    d = _load()
    n = _norm(url)
    if not n:
        return None
    key = n if n in d["links"] else d["aliases"].get(n)
    rec = d["links"].get(key) if key else None
    if rec is None:
        return None
    rec["hits"] = rec.get("hits", 0) + 1
    rec["last_seen_at"] = _now()
    _save(d)
    return rec


def store(payload: dict) -> dict:
    """写入/更新一条记录（非空字段覆盖、first_parsed_at 保留、sinaurl 建别名）。"""
    d = _load()
    n = _norm(payload.get("url") or "")
    if not n:
        raise SystemExit("link_cache: store 缺少必填字段 'url'")
    rec = d["links"].get(n) or {}
    rec.setdefault("first_parsed_at", _now())
    rec["last_parsed_at"] = _now()
    rec["url"] = n
    for k in _FIELDS:
        v = payload.get(k)
        if v not in (None, ""):
            rec[k] = v
    raw_sina = str(payload.get("sinaurl") or "").strip()
    sina_n = _norm(raw_sina)
    if sina_n:
        rec["sinaurl"] = sina_n
        d["aliases"][sina_n] = n
        if raw_sina != sina_n:  # 原样形式也登记，双保险
            d["aliases"][raw_sina] = n
    rec.setdefault("hits", 0)
    d["links"][n] = rec
    _save(d)
    return rec


def main(argv) -> int:
    if len(argv) < 2 or argv[1] not in ("check", "store"):
        print(__doc__.strip())
        return 2
    if argv[1] == "check":
        if len(argv) < 3:
            print(__doc__.strip())
            return 2
        for u in argv[2:]:
            rec = lookup(u)
            if rec:
                print("HIT\t" + u + "\t" + json.dumps(rec, ensure_ascii=False))
            else:
                print("MISS\t" + u)
        return 0
    raw = sys.stdin.read() if len(argv) > 2 and argv[2] == "-" else argv[2]
    rec = store(json.loads(raw))
    print("OK\t" + json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
