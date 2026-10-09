#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify response_20261008_1030.md: three 完整原文 blocks vs wb_verify JSONs, plus decoration checks."""
import json
import os
import re

BASE = os.path.expanduser("~/hermes_data/weibo_data")
with open(f"{BASE}/response_20261008_1030.md", encoding="utf-8") as f:
    resp = f.read()

ids = ["5351689555283007", "5351693232899262", "5351693445235128"]
blocks = re.findall(r"📄 完整原文\n(.+?)\n\n(?:📎 注|\*\*@卢麒元)", resp, re.S)
print("blocks found:", len(blocks))

ok = True
for i, wid in enumerate(ids):
    with open(f"{BASE}/wb_verify_{wid}.json", encoding="utf-8") as f:
        vj = json.load(f)
    base = vj.get("raw_text") or (vj.get("text_stripped") or "").rstrip()
    b = blocks[i] if i < len(blocks) else ""
    if b == base:
        print(f"P{i+1} OK len={len(base)}")
    else:
        ok = False
        print(f"P{i+1} MISMATCH: block_len={len(b)} base_len={len(base)}")
        n = min(len(b), len(base))
        for j in range(n):
            if b[j] != base[j]:
                print("  first diff at", j)
                print("   block:", repr(b[max(0, j - 30):j + 30]))
                print("   base :", repr(base[max(0, j - 30):j + 30]))
                break
        else:
            print("   prefix/tail diff:")
            print("   block tail:", repr(b[-50:]))
            print("   base  tail:", repr(base[-50:]))

for s in ["🎙️ 语音由 Windows TTS 生成（第1级）", "MEDIA:/tmp/weibo_voice.wav",
          "**@卢麒元 · 新微博 · 10-08 10:14:42", "**@卢麒元 · 新微博 · 10-08 10:29:18",
          "**@卢麒元 · 新微博 · 10-08 10:30:09", "📎 注"]:
    print(("FOUND " if s in resp else "MISSING ") + s[:40])

print("ALL OK" if ok else "HAS ERRORS")
