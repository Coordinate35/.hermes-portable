#!/usr/bin/env python3
"""Decode the nested data-fn-args JSON from the doubao share page (v2)."""
import re, html as h, json

html_txt = open('/tmp/doubao_thread.html', encoding='utf-8', errors='replace').read()

pos = html_txt.find('message_snapshot')
s_start = html_txt.rfind('<script', 0, pos)
a_start = html_txt.find('data-fn-args="', s_start) + len('data-fn-args="')
a_end = html_txt.find('"', a_start)
raw = html_txt[a_start:a_end]
print("raw attr len:", len(raw))
print("raw head:", raw[:200])
print("raw tail:", raw[-200:])

s1 = h.unescape(raw)
print("after html.unescape len:", len(s1))

data = json.loads(s1)
print("TOP-LEVEL PARSE OK, type:", type(data).__name__, "len:", len(data) if hasattr(data, '__len__') else '')

# walk to find the dict containing message_snapshot
found = []
def walk(x, path=""):
    if isinstance(x, dict):
        if 'message_snapshot' in x:
            found.append((path, x))
        for k, v in x.items():
            walk(v, path + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, path + f"[{i}]")
walk(data)
print("message_snapshot found at:", [p for p, _ in found])

# also find shareInfo-ish dicts
found2 = []
def walk2(x, path=""):
    if isinstance(x, dict):
        ks = set(x.keys())
        interesting = ks & {'share_id', 'share_time', 'message_snapshot', 'share_info', 'nick_name', 'item_list', 'content', 'common_info'}
        if 'share_id' in ks or 'message_snapshot' in ks or 'item_list' in ks:
            found2.append((path, list(ks)[:25]))
        for k, v in x.items():
            walk2(v, path + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk2(v, path + f"[{i}]")
walk2(data)
for p, ks in found2[:20]:
    print("DICT at", p, "->", ks)

with open('/home/coordinate35/hermes_data/doubao_parse/decoded_top.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("saved decoded_top.json, total len:", len(json.dumps(data, ensure_ascii=False)))
