#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""枚举百度地图某地名下的 POI（含各类「门」），用于回答「这个小区有哪些门」。

用法：
    PYTHONPATH= /usr/bin/python3 scripts/bd_poi_enum.py 展春园

原理：百度联想接口 su 返回 JSON，``s`` 数组每项按 ``$`` 切分，第 4 段（index 3）是名称。
覆盖不全，命中的只是百度收录过的门，结论里要注明这一点。
"""
import json
import sys
import urllib.parse
import urllib.request

URL = (
    "https://map.baidu.com/su?wd={wd}&cid=131&type=0&newmap=1"
    "&ie=utf-8&oue=1&fromproduct=jsapi&res=api"
)
SUFFIXES = [
    "", "小区", "小区-", "小区门", "小区北", "小区南", "小区东", "小区西",
    "小区东南", "小区西南", "小区东北", "小区西北",
    "北门", "南门", "东门", "西门",
]


def query(keyword):
    wd = urllib.parse.quote(keyword)
    req = urllib.request.Request(
        URL.format(wd=wd),
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://map.baidu.com/"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r).get("s", [])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    keyword = sys.argv[1]
    names = {}
    for suf in SUFFIXES:
        for item in query(keyword + suf):
            parts = item.split("$")
            if len(parts) > 3 and parts[3].strip():
                names.setdefault(parts[3].strip(), keyword + suf)

    gates = sorted(n for n in names if "门" in n)
    print(f"共 {len(names)} 个 POI，其中含「门」{len(gates)} 个\n")
    for n in gates:
        print("  ", n)
    print("\n其他相关 POI：")
    for n in sorted(x for x in names if "门" not in x):
        print("  ", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
