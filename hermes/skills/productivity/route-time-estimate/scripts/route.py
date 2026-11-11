#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Photon 地名 → FOSSGIS OSRM 路线：步行/骑行/驾车 距离与耗时。

用法:
  route.py "抖音大钟寺广场2号楼" "展春园小区"
  route.py "116.33706,39.96450" "116.33681,39.98558"   # lon,lat
"""
import json
import math
import sys
import time
import urllib.parse
import urllib.request

UA = "hermes-route/1.0"
PROFILES = [("步行", "routed-foot", "foot"),
            ("骑行", "routed-bike", "bike"),
            ("驾车", "routed-car", "driving")]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def geocode(q):
    url = "https://photon.komoot.io/api/?q=%s&limit=1" % urllib.parse.quote(q)
    feats = get(url).get("features") or []
    if not feats:
        raise SystemExit("地名未命中: %s" % q)
    f = feats[0]
    lon, lat = f["geometry"]["coordinates"][:2]
    p = f.get("properties") or {}
    label = " ".join(x for x in [p.get("name"), p.get("district")] if x)
    return (lon, lat), label or q


def as_point(s):
    parts = s.split(",")
    if len(parts) == 2:
        try:
            return (float(parts[0]), float(parts[1])), s
        except ValueError:
            pass
    return geocode(s)


def haversine(a, b):
    lon1, lat1 = a
    lon2, lat2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def leg(a, b, prefix, profile):
    url = ("https://routing.openstreetmap.de/%s/route/v1/%s/%s,%s;%s,%s?overview=false"
           % (prefix, profile, a[0], a[1], b[0], b[1]))
    r = get(url)["routes"][0]
    return r["distance"] / 1000.0, r["duration"] / 60.0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    a, an = as_point(argv[1])
    b, bn = as_point(argv[2])
    print("起点: %s  %.5f,%.5f" % (an, a[0], a[1]))
    print("终点: %s  %.5f,%.5f" % (bn, b[0], b[1]))
    print("直线: %.2f km" % haversine(a, b))
    for label, prefix, profile in PROFILES:
        try:
            km, minutes = leg(a, b, prefix, profile)
            print("%s: %.2f km, %.0f min" % (label, km, minutes))
        except Exception as e:  # noqa: BLE001 - 单一 profile 失败不影响其他
            print("%s: ERR %s" % (label, e))
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
