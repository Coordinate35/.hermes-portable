#!/usr/bin/env python3
"""核验 5345934040891998：show / pc longtext / render 三源 + 转发卡片信息。"""
import sys, json, re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

wid = '5345934040891998'
out = {}
UA = w.HEADERS.get('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')

# --- 1. show API ---
try:
    h1 = {'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest', 'Referer': f'https://m.weibo.cn/detail/{wid}'}
    r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}', headers=h1, cookies=w.COOKIES, timeout=15)
    d = r.json()
    data = d.get('data', {}) or {}
    show = {
        'status': r.status_code,
        'repost_type': data.get('repost_type'),
        'isLongText': data.get('isLongText'),
        'raw_text': data.get('raw_text'),
        'text_tail': (data.get('text') or '')[-120:],
        'longTextContent_tail': (data.get('longTextContent') or '')[-120:],
    }
    rs = data.get('retweeted_status')
    if rs:
        show['rt'] = {
            'id': rs.get('id'),
            'user': ((rs.get('user') or {}).get('screen_name')),
            'isLongText': rs.get('isLongText'),
            'text_head': (rs.get('text') or '')[:120],
            'longTextContent_head': (rs.get('longTextContent') or '')[:120],
            'longTextContent_tail': (rs.get('longTextContent') or '')[-100:],
        }
    out['show'] = show
except Exception as e:
    out['show'] = {'ok': False, 'err': str(e)}

# --- 2. pc longtext ---
try:
    h2 = {'User-Agent': UA, 'Referer': 'https://weibo.com/'}
    r2 = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={wid}', headers=h2, cookies=w.COOKIES, timeout=15)
    try:
        d2 = r2.json()
        lc = (d2.get('data') or {}).get('longTextContent') or ''
        out['pc_longtext'] = {'status': r2.status_code, 'ok': d2.get('ok'), 'tail': lc[-100:], 'full_len': len(lc)}
    except Exception:
        out['pc_longtext'] = {'status': r2.status_code, 'raw_head': r2.text[:300]}
except Exception as e:
    out['pc_longtext'] = {'ok': False, 'err': str(e)}

# --- 3. render page ---
try:
    r3 = requests.get(f'https://m.weibo.cn/status/{wid}?_=2', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
    html = r3.text
    cnt = {m: html.count(m) for m in ['展开全文', '回血', '血条', '不容易', '社会主义在中东', '多问一句']}
    seg = {}
    for m in ['回血', '不容易']:
        idxs = [mm.start() for mm in re.finditer(re.escape(m), html)]
        seg[m] = []
        for i in idxs[:4]:
            s = html[max(0, i-80):i+150].replace('\n', ' ')
            seg[m].append(s)
    rd = {}
    mrd = re.search(r'var \$render_data = (\[.*?\]);', html, re.S)
    if mrd:
        try:
            j = json.loads(mrd.group(1))
            st = (j[0] or {}).get('status') or {}
            rd = {'text_tail': (st.get('text') or '')[-150:], 'raw_text_tail': (st.get('raw_text') or '')[-150:],
                  'longTextContent_tail': (st.get('longTextContent') or '')[-150:], 'repost_type': st.get('repost_type')}
        except Exception as e:
            rd = {'parse_err': str(e)}
    out['render'] = {'status': r3.status_code, 'len': len(html), 'counts': cnt, 'segments': seg, 'render_data': rd}
except Exception as e:
    out['render'] = {'ok': False, 'err': str(e)}

print(json.dumps(out, ensure_ascii=False, indent=1))
