#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""枚举百度地图里某个小区/POI 的所有「门」。

用法:
    PYTHONPATH= /usr/bin/python3 enumerate_gates.py "展春园小区" [城市码=131]
输出:
    每行一个门名，最后一行给出总数。
"""
import json
import sys
import urllib.parse
import urllib.request

URL = "https://map.baidu.com/su?wd={wd}&cid={cid}&type=0&newmap=1&ie=utf-8&oue=1&fromproduct=jsapi&res=api"


def suggest(wd, cid):
    url = URL.format(wd=urllib.parse.quote(wd), cid=cid)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://map.baidu.com/"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "展春园小区"
    cid = sys.argv[2] if len(sys.argv) > 2 else "131"

    queries = [base, f"{base}-", f"{base}门", f"{base}大门"]
    for d in ["东", "西", "南", "北", "东南", "西南", "东北", "西北"]:
        queries += [f"{base}{d}", f"{base}{d}门"]
    queries += [f"{base}1门", f"{base}2门", f"{base}二门"]

    found = {}
    for q in queries:
        try:
            d = suggest(q, cid)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] {q}: {e}", file=sys.stderr)
            continue
        for s in d.get("s", []):
            parts = s.split("$")
            if len(parts) > 3:
                nm = parts[3].strip()
                if nm.startswith(base) and "门" in nm:
                    found.setdefault(nm, q)

    for nm in sorted(found):
        print(nm)
    print(f"# total={len(found)}")


if __name__ == "__main__":
    main()
