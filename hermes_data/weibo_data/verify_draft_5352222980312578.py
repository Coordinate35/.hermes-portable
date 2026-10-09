#!/usr/bin/env python3
"""拟交付稿 block 与 show raw_text（t.cn→显示文案替换）逐字节校验；并落盘规范化 baseline JSON 供 wb_diff_check。"""
import json
import re

DRAFT = "/home/coordinate35/hermes_data/weibo_data/delivery_20261009_2135.txt"
VJ = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5352222980312578.json"
NORM = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5352222980312578.norm.json"

URL = "http://t.cn/AXlUveQJ"
DISPLAY = "查看图片"

draft = open(DRAFT, encoding="utf-8").read()
vj = json.load(open(VJ, encoding="utf-8"))
raw = vj.get("raw_text") or ""
print("raw contains url:", URL in raw, "| occ:", raw.count(URL))
exp = raw.replace(URL, DISPLAY)
print("exp  :", repr(exp))
print("exp len:", len(exp))

m = re.search(r"📄 完整原文\n(.+?)\n\n(?:📎 注|【转发 )", draft, re.S)
block = m.group(1) if m else None
print("block:", repr(block))

if block is None:
    print("EXTRACT FAIL")
else:
    print("MATCH:", block == exp)
    if block != exp:
        n = min(len(block), len(exp))
        for i in range(n):
            if block[i] != exp[i]:
                print("first mismatch at", i)
                print("  block:", repr(block[max(0, i - 30):i + 30]))
                print("  exp  :", repr(exp[max(0, i - 30):i + 30]))
                break
        else:
            print("prefix-only diff; tails:", repr(block[n:]), repr(exp[n:]))

vj2 = dict(vj)
vj2["raw_text"] = exp
with open(NORM, "w", encoding="utf-8") as f:
    json.dump(vj2, f, ensure_ascii=False, indent=1)
print("norm json written:", NORM)
