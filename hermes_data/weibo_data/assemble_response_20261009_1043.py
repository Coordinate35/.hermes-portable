#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble final response for weibo round 2026-10-09 10:43 (id 5352059115406034).

Usage: python3 assemble_response_20261009_1043.py "<voice level line>"
"""
import os
import sys

BASE = os.path.expanduser("~/hermes_data/weibo_data")
WID = "5352059115406034"

draft = open(f"{BASE}/draft_{WID}.md", encoding="utf-8").read()
level = sys.argv[1] if len(sys.argv) > 1 else "⚠️ 语音生成失败"
if level.startswith("⚠️"):
    resp = draft + "\n⚠️ 语音生成失败\n"
else:
    resp = draft + f"\n{level}\nMEDIA:/tmp/weibo_voice.wav\n"

with open(f"{BASE}/response_20261009_1043.md", "w", encoding="utf-8") as f:
    f.write(resp)

print("OK len:", len(resp))
print(resp)
