#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 share_payload2 的答案文本解析金油比数据表 -> CSV（utf-8-sig）。
用法: python3 gen_ratio_csv.py <share_payload.json> <out.csv>
"""
import json, re, sys, os

pay = json.load(open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
msgs = pay["data"]["message_snapshot"]["message_list"]
text = None
for m in msgs:
    blocks = json.loads(m.get("content") or "[]")
    for b in blocks:
        if b.get("block_type") == 10000:
            t = b["content"]["text_block"].get("text", "")
            if "金油比" in t and "|" in t:
                text = t
if not text:
    print("TABLE_NOT_FOUND")
    sys.exit(1)

rows = []
for ln in text.split("\n"):
    s = ln.strip()
    m = re.match(r"^\|(\d{4})\|([\d.]+)\|(.+)\|$", s)
    if m:
        year, ratio, event = m.group(1), m.group(2), m.group(3).replace("**", "")
        rows.append((year, ratio, event))

print("rows parsed:", len(rows))
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8-sig") as f:
    f.write("年份,金油比（1盎司黄金=？桶原油）,核心事件/解读\n")
    for year, ratio, event in rows:
        f.write(f'{year},{ratio},"{event}"\n')
print("saved:", out)
