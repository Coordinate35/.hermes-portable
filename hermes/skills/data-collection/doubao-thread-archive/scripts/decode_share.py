#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从豆包分享页 HTML 解码完整数据。
用法: python3 decode_share.py <share_page.html> <out_share_payload.json>
原理: 数据嵌在 <script data-fn-name="mergeLoaderData" data-fn-args="..."> 属性里，
多层转义: html.unescape -> json.loads -> routerDataFnArgs 字符串再 json.loads。
"""
import re, html as h, json, sys

src, out = sys.argv[1], sys.argv[2]
html_txt = open(src, encoding="utf-8", errors="replace").read()

pos = html_txt.find("message_snapshot")
if pos < 0:
    print("ERROR: 页面中未找到 message_snapshot（可能不是分享页，或页面结构变化）")
    sys.exit(1)
s_start = html_txt.rfind("<script", 0, pos)
if s_start < 0:
    print("ERROR: 未找到包含数据的 script 标签")
    sys.exit(1)
a_start = html_txt.find('data-fn-args="', s_start)
if a_start < 0:
    print("ERROR: script 标签中未找到 data-fn-args 属性")
    sys.exit(1)
a_start += len('data-fn-args="')
# 属性值内可能含 '>'，必须用引号定位结尾
a_end = html_txt.find('"', a_start)
raw = html_txt[a_start:a_end]
print("data-fn-args length:", len(raw))

data = json.loads(h.unescape(raw))

payloads = []

def walk(x):
    if isinstance(x, dict):
        if "routerDataFnArgs" in x:
            args = x["routerDataFnArgs"]
            for a in (args if isinstance(args, list) else [args]):
                if isinstance(a, str) and "message_snapshot" in a:
                    payloads.append(json.loads(a))
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(data)
if not payloads:
    print("ERROR: 未找到 share payload（routerDataFnArgs 中）")
    sys.exit(2)

main = payloads[0]
json.dump(main, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = len(main["data"]["message_snapshot"]["message_list"])
print("saved:", out)
print("share_name:", main["data"]["share_info"].get("share_name"))
print("messages:", n)
