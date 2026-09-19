#!/usr/bin/env python3
"""渲染页细节复核：两帖 render 页中 '讳莫如深' / '并借' 各处上下文及结尾。"""
import sys, json, re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

UA = w.HEADERS.get('User-Agent', 'Mozilla/5.0')
out = {}
for wid in ['5344943035909706', '5344943112454432']:
    o = {}
    o['raw_full'] = None
    try:
        h1 = {'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest', 'Referer': f'https://m.weibo.cn/detail/{wid}'}
        r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}', headers=h1, cookies=w.COOKIES, timeout=15)
        data = r.json().get('data', {}) or {}
        o['raw_full'] = data.get('raw_text')
    except Exception as e:
        o['show_err'] = repr(e)
    for tag, q in [('r2', '?_=2'), ('r3', '?_=3')]:
        try:
            rr = requests.get(f'https://m.weibo.cn/status/{wid}{q}', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
            html = rr.text
            ctxs = {}
            for m in ['并借', '讳莫如深', '此地无银', '太闲了', '镜鉴']:
                idxs = [mm.start() for mm in re.finditer(re.escape(m), html)]
                ctxs[m] = {'count': len(idxs),
                           'ctx': [html[max(0, i-30):i+90].replace('\n', ' ') for i in idxs[:4]]}
            o[tag] = {'len': len(html), 'ctx': ctxs}
        except Exception as e:
            o[tag] = {'err': repr(e)}
    out[wid] = o

print(json.dumps(out, ensure_ascii=False, indent=1))
