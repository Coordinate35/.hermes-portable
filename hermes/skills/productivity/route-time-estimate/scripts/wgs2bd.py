#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WGS84 -> GCJ02 -> BD09 坐标转换。

百度地图用 BD-09；直接把 OSM/photon 给的 WGS84 坐标喂给百度会偏 ~500 m。
仅当要按经纬度调用百度时使用；用地名+联想项调路线不需要。

用法:
    PYTHONPATH= /usr/bin/python3 wgs2bd.py 116.33706,39.96450
输出: BD09 纬度,经度（百度 latlng 参数是 lat,lon 顺序）
"""
import math
import sys

X_PI = math.pi * 3000.0 / 180.0
A = 6378245.0
EE = 0.00669342162296594323


def _tlat(x, y):
    r = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    r += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return r


def _tlng(x, y):
    r = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    r += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return r


def wgs2gcj(lng, lat):
    dlat = _tlat(lng - 105.0, lat - 35.0)
    dlng = _tlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = 1 - EE * math.sin(radlat) ** 2
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat


def gcj2bd(lng, lat):
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * X_PI)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * X_PI)
    return z * math.cos(theta) + 0.0065, z * math.sin(theta) + 0.006


def wgs2bd(lng, lat):
    return gcj2bd(*wgs2gcj(lng, lat))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    lng_s, lat_s = sys.argv[1].split(",")
    lng, lat = float(lng_s), float(lat_s)
    blng, blat = wgs2bd(lng, lat)
    print(f"WGS84 {lng:.6f},{lat:.6f} -> BD09 lat={blat:.6f},lon={blng:.6f}")
