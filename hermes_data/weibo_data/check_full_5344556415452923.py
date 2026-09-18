#!/usr/bin/env python3
"""三方互核：m.weibo.cn show API / pc longtext / m.weibo.cn 渲染页源码。
用法: python3 check_full_5344556415452923.py
"""
import sys, json, re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

wid = '5344556415452923'
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
        'text': data.get('text'),
        'longTextContent': data.get('longTextContent'),
    }
    rs = data.get('retweeted_status')
    if rs:
        show['rt_user'] = ((rs.get('user') or {}).get('screen_name'))
        show['rt_id'] = rs.get('id')
        show['rt_isLongText'] = rs.get('isLongText')
        show['rt_text_head'] = (rs.get('text') or '')[:150]
    out['show'] = show
except Exception as e:
    out['show'] = {'ok': False, 'err': str(e)}

# --- 2. pc longtext ---
try:
    h2 = {'User-Agent': UA, 'Referer': 'https://weibo.com/'}
    r2 = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={wid}', headers=h2, cookies=w.COOKIES, timeout=15)
    try:
        d2 = r2.json()
        out['pc_longtext'] = {'status': r2.status_code, 'ok': d2.get('ok'),
                              'longTextContent': (d2.get('data') or {}).get('longTextContent')}
    except Exception:
        out['pc_longtext'] = {'status': r2.status_code, 'raw_head': r2.text[:300]}
except Exception as e:
    out['pc_longtext'] = {'ok': False, 'err': str(e)}

# --- 3. render page ---
try:
    r3 = requests.get(f'https://m.weibo.cn/status/{wid}?_=2', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
    html = r3.text
    cnt = {m: html.count(m) for m in ['展开全文', '平成战败', '匪夷所思', '斗兽场', '央视财经', '美联储', '中海油', '金殖']}
    seg = {}
    for m in ['平成战败', '匪夷所思', '斗兽场']:
        idxs = [mm.start() for mm in re.finditer(re.escape(m), html)]
        seg[m] = []
        for i in idxs[:4]:
            s = html[max(0, i-60):i+200].replace('\n', ' ')
            seg[m].append(s)
    # try parse $render_data
    rd = {}
    mrd = re.search(r'var \$render_data = (\[.*?\]);', html, re.S)
    if mrd:
        try:
            j = json.loads(mrd.group(1))
            st = (j[0] or {}).get('status') or {}
            rd = {'text': st.get('text'), 'raw_text': st.get('raw_text'),
                  'longTextContent': st.get('longTextContent'), 'repost_type': st.get('repost_type')}
        except Exception as e:
            rd = {'parse_err': str(e)}
    out['render'] = {'status': r3.status_code, 'len': len(html), 'counts': cnt, 'segments': seg, 'render_data': rd}
except Exception as e:
    out['render'] = {'ok': False, 'err': str(e)}

print(json.dumps(out, ensure_ascii=False, indent=1))
