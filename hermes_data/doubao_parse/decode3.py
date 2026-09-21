#!/usr/bin/env python3
"""Full decoder: extract share info + all messages + files/URLs."""
import re, html as h, json

html_txt = open('/tmp/doubao_thread.html', encoding='utf-8', errors='replace').read()
pos = html_txt.find('message_snapshot')
s_start = html_txt.rfind('<script', 0, pos)
a_start = html_txt.find('data-fn-args="', s_start) + len('data-fn-args="')
a_end = html_txt.find('"', a_start)
raw = html_txt[a_start:a_end]

data = json.loads(h.unescape(raw))

# find share payload: walk for dicts with 'routerDataFnArgs'
payloads = []
def walk(x, path=""):
    if isinstance(x, dict):
        if 'routerDataFnArgs' in x:
            args = x['routerDataFnArgs']
            for i, a in enumerate(args if isinstance(args, list) else [args]):
                if isinstance(a, str) and 'message_snapshot' in a:
                    try:
                        payloads.append(json.loads(a))
                    except Exception as e:
                        print("load fail:", e)
        for k, v in x.items():
            walk(v, path + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, path + f"[{i}]")
walk(data)

print("payloads found:", len(payloads))
for p in payloads:
    print("payload keys:", list(p.keys())[:40])

# save the main payload
if payloads:
    main = payloads[0]
    with open('/home/coordinate35/hermes_data/doubao_parse/share_payload.json', 'w', encoding='utf-8') as f:
        json.dump(main, f, ensure_ascii=False, indent=1)
    print("saved share_payload.json")

# inspect structure of payload
main = payloads[0]
print("\n=== payload skeleton ===")
def skel(x, d=0, maxd=4, prefix=''):
    if d > maxd: return
    p = '  ' * d
    if isinstance(x, dict):
        for k, v in x.items():
            t = type(v).__name__
            if isinstance(v, dict):
                print(f"{p}{k}: dict({len(v)})")
                skel(v, d+1, maxd, prefix+k+'/')
            elif isinstance(v, list):
                print(f"{p}{k}: list({len(v)})")
                if v and isinstance(v[0], dict):
                    print(f"{p}  [0] keys: {list(v[0].keys())[:15]}")
            else:
                sv = str(v)
                print(f"{p}{k} = {sv[:100]!r}")
skel(main)
