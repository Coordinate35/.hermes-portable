#!/usr/bin/env python3
"""核验两帖权威文本与止点（show / pc longtext / m.weibo.cn 渲染三方）。
用法: python3 check_full_2cur_20260919_1931.py
"""
import sys, json, re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

IDS = ['5344943035909706', '5344943112454432']  # B(19:26:26) first, A(19:26:44)
UA = w.HEADERS.get('User-Agent', 'Mozilla/5.0')

def tail(s, n=80):
    s = s or ''
    return s[-n:]

out = {}
for wid in IDS:
    o = {}
    # --- 1. show API ---
    try:
        h1 = {'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest', 'Referer': f'https://m.weibo.cn/detail/{wid}'}
        r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}', headers=h1, cookies=w.COOKIES, timeout=15)
        d = r.json()
        data = d.get('data', {}) or {}
        t = data.get('text') or ''
        rt = data.get('raw_text') or ''
        lt = data.get('longTextContent') or ''
        o['show'] = {
            'status': r.status_code,
            'repost_type': data.get('repost_type'),
            'isLongText': data.get('isLongText'),
            'text_full': t, 'text_len': len(t), 'text_tail': tail(t),
            'raw_len': len(rt), 'raw_tail': tail(rt),
            'lt_len': len(lt), 'lt_tail': tail(lt),
            'flags': {m: (m in t) for m in ['太闲了', '并借鉴', '讳莫如深', '蜡烛']},
        }
        rs = data.get('retweeted_status')
        if rs:
            o['show']['rt'] = {'id': rs.get('id'), 'user': (rs.get('user') or {}).get('screen_name'),
                               'text_head': (rs.get('text') or '')[:100]}
    except Exception as e:
        o['show'] = {'err': repr(e)}
    # --- 2. pc longtext ---
    try:
        h2 = {'User-Agent': UA, 'Referer': 'https://weibo.com/'}
        r2 = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={wid}', headers=h2, cookies=w.COOKIES, timeout=15)
        try:
            d2 = r2.json()
            c = (d2.get('data') or {}).get('longTextContent') or ''
            o['pc_longtext'] = {'status': r2.status_code, 'ok': d2.get('ok'), 'len': len(c),
                                'tail': tail(c), 'has_bingJiejian': '并借鉴' in c}
        except Exception:
            o['pc_longtext'] = {'status': r2.status_code, 'raw_head': r2.text[:200]}
    except Exception as e:
        o['pc_longtext'] = {'err': repr(e)}
    # --- 3. render page ---
    try:
        r3 = requests.get(f'https://m.weibo.cn/status/{wid}?_=2', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
        html = r3.text
        cnt = {m: html.count(m) for m in ['展开全文', '太闲了', '并借鉴', '讳莫如深', '蜡烛', '鲜花']}
        seg = {}
        for m in ['并借鉴', '太闲了']:
            idxs = [mm.start() for mm in re.finditer(re.escape(m), html)]
            seg[m] = [html[max(0, i-80):i+120].replace('\n', ' ') for i in idxs[:2]]
        rd = {}
        mrd = re.search(r'var \$render_data = (\[.*?\]);', html, re.S)
        if mrd:
            try:
                j = json.loads(mrd.group(1))
                st = (j[0] or {}).get('status') or {}
                rd = {'text_len': len(st.get('text') or ''), 'text_tail': tail(st.get('text')),
                      'raw_text_len': len(st.get('raw_text') or ''), 'raw_text_tail': tail(st.get('raw_text')),
                      'ltc_len': len(st.get('longTextContent') or ''), 'ltc_tail': tail(st.get('longTextContent'))}
            except Exception as e:
                rd = {'parse_err': repr(e)}
        o['render'] = {'status': r3.status_code, 'len': len(html), 'counts': cnt, 'segments': seg, 'render_data': rd}
    except Exception as e:
        o['render'] = {'err': repr(e)}
    out[wid] = o

print(json.dumps(out, ensure_ascii=False, indent=1))
