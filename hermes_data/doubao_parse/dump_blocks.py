#!/usr/bin/env python3
"""Dump every block in the share message list with details."""
import json

pay = json.load(open('/home/coordinate35/hermes_data/doubao_parse/share_payload.json', encoding='utf-8'))
msgs = pay['data']['message_snapshot']['message_list']
print("message count:", len(msgs))

for mi, m in enumerate(msgs):
    print("="*100)
    print(f"MSG #{mi}  user_type={m.get('user_type')}  msg_id={m.get('message_id')}  index={m.get('index_in_conv')}  time={m.get('create_time')}")
    # both content (legacy) and content_block
    content = m.get('content') or ''
    try:
        blocks = json.loads(content)
    except Exception as e:
        blocks = []
        print("content parse fail:", e)
    if isinstance(blocks, dict):
        blocks = [blocks]
    print(f"content blocks: {len(blocks)}")
    for bi, b in enumerate(blocks):
        bt = b.get('block_type')
        c = b.get('content') or {}
        if not isinstance(c, dict):
            print(f"  [{bi}] type={bt} content-not-dict: {str(c)[:200]}")
            continue
        kinds = list(c.keys())
        print(f"  [{bi}] type={bt} keys={kinds}")
        if bt == 10000 and 'text_block' in c:
            t = c['text_block'].get('text', '')
            print(f"      TEXT({len(t)}): {t[:400]!r}")
        elif bt == 10040 and 'thinking_block' in c:
            tb = c['thinking_block']
            print(f"      THINK: {tb.get('finish_title')!r}")
        elif bt == 10019 and 'file_operation_block' in c:
            fb = c['file_operation_block']
            print(f"      FILEOP: op={fb.get('operation_type')} path={fb.get('path','')[:120]!r}")
            print(f"      header_summary: {str(fb.get('header',{}).get('summary',''))[:150]!r}")
            print(f"      content[:600]: {str(fb.get('content',''))[:600]!r}")
            print(f"      file_name: {fb.get('file_name')!r} file_type: {fb.get('file_type')!r}")
        elif bt == 10025 and 'search_query_result_block' in c:
            sb = c['search_query_result_block']
            print(f"      SEARCH: {sb.get('summary')!r} queries={sb.get('queries')}")
            for r in (sb.get('results') or [])[:20]:
                tc = r.get('text_card') or {}
                print(f"         - {tc.get('title','')[:80]!r} {str(tc.get('url',''))[:120]}")
        elif bt == 10030 and 'artifact_block' in c:
            ab = c['artifact_block']
            print(f"      ARTIFACT: title={ab.get('title')!r} res_id={ab.get('resource_id')} type={ab.get('resource_type')}")
            print(f"      meta: {json.dumps(ab, ensure_ascii=False)[:800]}")
        else:
            print(f"      FULL: {json.dumps(c, ensure_ascii=False)[:700]}")
    # also content_block duplicates - skip detail but note count
    cb = m.get('content_block')
    if cb:
        print(f"  content_block count: {len(cb)}, types: {[x.get('block_type') for x in cb]}")
