#!/usr/bin/env python3
# Probe raw_text exact bytes from wb_verify JSON (read-only).
import json

p = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5353129186166258.json"
vj = json.load(open(p, encoding="utf-8"))
raw = vj.get("raw_text")
stripped = vj.get("text_stripped")
print("raw_len:", len(raw))
print("raw_repr_head:", repr(raw[:40]))
print("raw_repr_tail:", repr(raw[-40:]))
print("stripped_len:", len(stripped))
print("equal_raw_vs_stripped:", raw == stripped)
print("raw_has_newline:", "\n" in raw)
print("raw_has_brackets:", "[" in raw or "]" in raw)
lg = vj.get("long_text")
pc = vj.get("pc_longtext")
print("long_text_equal_raw:", lg == raw)
print("pc_longtext_equal_raw:", pc == raw)
print("repost_type:", vj.get("repost_type"))
