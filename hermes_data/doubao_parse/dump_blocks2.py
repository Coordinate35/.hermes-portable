#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速 dump share payload 的概要信息（消息块/文件/链接）。"""
import json, sys, re
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8))

path = sys.argv[1]
pay = json.load(open(path, encoding="utf-8"))
share = pay["data"]["share_info"]
msgs = pay["data"]["message_snapshot"]["message_list"]
st = datetime.fromtimestamp(int(share["share_time"]) / 1000, tz=CST)
print("share_name:", share.get("share_name"))
print("user:", share["user"]["nick_name"], "| share_time:", st.strftime("%Y-%m-%d %H:%M"), "| messages:", len(msgs))
print("=" * 80)
for mi, m in enumerate(msgs):
    ut = m.get("user_type")
    t = datetime.fromtimestamp(int(m.get("create_time", 0)), tz=CST).strftime("%H:%M:%S")
    print(f"[MSG {mi}] user_type={ut} time={t}")
    try:
        blocks = json.loads(m.get("content") or "[]")
    except Exception as e:
        print("  parse fail:", e); continue
    for bi, b in enumerate(blocks):
        bt = b.get("block_type")
        c = b.get("content") or {}
        if bt == 10000:
            t_ = c.get("text_block", {}).get("text", "")
            print(f"  [{bi}] TEXT({len(t_)}): {t_[:200]!r}")
        elif bt == 10040:
            print(f"  [{bi}] THINK: {c.get('thinking_block',{}).get('finish_title')!r}")
        elif bt == 10019:
            fb = c.get("file_operation_block", {})
            summ = (fb.get("header") or {}).get("summary", "")
            content = str(fb.get("content") or "")
            print(f"  [{bi}] FILEOP({fb.get('operation_type')}) path={str(fb.get('path',''))[:100]!r} name={fb.get('file_name')!r}")
            print(f"       summary: {summ[:120]!r}")
            # spot feishu / urls in content
            for u in re.findall(r'https?://[^\s"\'\\<>\)\]]+', content)[:5]:
                print(f"       URL: {u[:150]}")
        elif bt == 10025:
            sb = c.get("search_query_result_block", {})
            print(f"  [{bi}] SEARCH: {sb.get('summary')!r} queries={sb.get('queries')}")
        elif bt == 10030:
            ab = c.get("artifact_block", {})
            print(f"  [{bi}] ARTIFACT: title={ab.get('title')!r} res_id={ab.get('resource_id')} type={ab.get('resource_type')} content_type={ab.get('resource_content_type')}")
        else:
            print(f"  [{bi}] type={bt} keys={list(c.keys())} preview={json.dumps(c, ensure_ascii=False)[:200]}")
