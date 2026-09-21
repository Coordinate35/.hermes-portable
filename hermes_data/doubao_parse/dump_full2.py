#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印 payload2 的完整文本块与搜索来源，写入 /tmp/payload2_full.txt"""
import json, sys
pay = json.load(open(sys.argv[1], encoding="utf-8"))
msgs = pay["data"]["message_snapshot"]["message_list"]
out = []
for mi, m in enumerate(msgs):
    out.append(f"########## MSG {mi} user_type={m.get('user_type')} ##########")
    blocks = json.loads(m.get("content") or "[]")
    for bi, b in enumerate(blocks):
        bt = b.get("block_type")
        c = b.get("content") or {}
        if bt == 10000:
            out.append(f"----- BLOCK {bi} TEXT -----")
            out.append(c["text_block"].get("text", ""))
        elif bt == 10025:
            sb = c.get("search_query_result_block", {})
            out.append(f"----- BLOCK {bi} SEARCH: {sb.get('summary')} -----")
            for q in (sb.get("queries") or []):
                out.append(f"QUERY: {q}")
            for i, r in enumerate(sb.get("results") or [], 1):
                tc = r.get("text_card") or {}
                out.append(f"{i}. {(tc.get('title') or '').strip()} — {tc.get('url')}")
        elif bt == 10040:
            out.append(f"----- BLOCK {bi} THINK: {c.get('thinking_block',{}).get('finish_title')} -----")
        else:
            out.append(f"----- BLOCK {bi} type={bt} -----")
            out.append(json.dumps(c, ensure_ascii=False, indent=1))
    # extras
    cb = m.get("content_block")
    if cb:
        out.append(f"----- content_block n={len(cb)} types={[x.get('block_type') for x in cb]} -----")
open("/tmp/payload2_full.txt", "w", encoding="utf-8").write("\n".join(out))
print("written /tmp/payload2_full.txt, lines:", len(out))
print("total chars:", len("\n".join(out)))
