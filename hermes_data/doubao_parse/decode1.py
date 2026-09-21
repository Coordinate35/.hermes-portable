#!/usr/bin/env python3
"""Decode the nested data-fn-args JSON from the doubao share page."""
import re, html as h, json, sys

html_txt = open('/tmp/doubao_thread.html', encoding='utf-8', errors='replace').read()

# find script tag with data-fn-args containing message_snapshot
pos = html_txt.find('message_snapshot')
s_start = html_txt.rfind('<script', 0, pos)
s_end = html_txt.find('>', s_start)  # end of opening tag
# extract attribute
tag = html_txt[s_start:s_end+1]
m = re.search(r'data-fn-args="(.*)"$', tag, re.S)
raw = m.group(1)
print("raw attr len:", len(raw))

s1 = h.unescape(raw)
print("after html.unescape len:", len(s1))
print("first 300:", s1[:300])

# try parsing as JSON
try:
    data = json.loads(s1)
    print("TOP-LEVEL PARSE OK, type:", type(data))
    if isinstance(data, list):
        print("list len:", len(data))
        # dump structure skeleton
        def skel(x, d=0, maxd=6):
            prefix = '  '*d
            if d > maxd: return
            if isinstance(x, dict):
                for k, v in list(x.items())[:20]:
                    t = type(v).__name__
                    if isinstance(v, (dict, list)):
                        print(prefix + f"{k}: {t}({len(v)})")
                        skel(v, d+1, maxd)
                    else:
                        sv = str(v)
                        print(prefix + f"{k}: {t} = {sv[:80]!r}")
            elif isinstance(x, list):
                for idx, v in enumerate(x[:5]):
                    print(prefix + f"[{idx}] {type(v).__name__}")
                    skel(v, d+1, maxd)
        skel(data)
except Exception as e:
    print("PARSE FAIL:", e)
    # maybe it's not full JSON; find the message_snapshot enclosing
    sys.exit(1)

# save
with open('/home/coordinate35/hermes_data/doubao_parse/decoded_top.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("saved decoded_top.json")
