#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染页核验：5353904092743131 渲染文本止点 + analysis_extra 全串"""
import re, requests, html as htmllib

url = "https://m.weibo.cn/status/5353904092743131?_=2"
headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"}
r = requests.get(url, headers=headers, timeout=25)
t = r.text
print("HTTP", r.status_code, "len", len(t))
print("visitor_wall:", "Sina Visitor System" in t and "SSO" in t)

# \uXXXX 解码副本（用于可读匹配）
uni = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), t)

def to_text(s):
    s = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*/?>', r'\1', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmllib.unescape(s)
    return s

# analysis_extra 全串
for pat in [r'"analysis_extra"\s*:\s*"([^"]*)"', r'mblog_parent_id[^|"&\s]*']:
    mm = re.findall(pat, uni)
    print("PAT", pat, "->", mm[:5])

# 渲染副本（"回复@邹江的微博" 出现处）
needle = "回复@邹江的微博"
positions = [mm.start() for mm in re.finditer(re.escape(needle), uni)]
print("copies:", len(positions))
for i, p in enumerate(positions):
    seg = to_text(uni[p:p+400])
    print(f"--- copy {i+1} @ {p} ---")
    print(repr(seg[:220]))

# 检查链尾是否还有更深 //@ 段
for mm in re.finditer(r'安心！', uni):
    p = mm.start()
    seg = to_text(uni[p:p+200])
    print("--- after 安心! ---")
    print(repr(seg[:150]))
