#!/usr/bin/env python3
"""核验 2026-09-24 15:51 轮 3 条新帖：show / pc longtext / extend / 渲染 + 时间线卡片。
IDs: 5346699084303732 (15:44:21), 5346699965104242 (15:47:50), 5346700325816668 (15:49:17)
"""
import sys
import json
import re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

IDS = ['5346699084303732', '5346699965104242', '5346700325816668']
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
OUT = {}

# 0) timeline window (page1)
tl = {}
try:
    url = ('https://m.weibo.cn/api/container/getIndex?uid=1245732825&type=uid'
           '&value=1245732825&containerid=1076031245732825')
    data = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=15).json()
    for c in data.get('data', {}).get('cards', []):
        if c.get('card_type') == 9:
            mb = c.get('mblog') or {}
            tl[str(mb.get('id'))] = mb
    print('timeline cards indexed:', len(tl))
except Exception as e:
    print('timeline fetch failed:', e)

for wid in IDS:
    o = {}
    mb = tl.get(wid)
    if mb:
        o['timeline'] = {
            'created_at': mb.get('created_at'),
            'source': mb.get('source'),
            'isLongText': mb.get('isLongText'),
            'raw_text': mb.get('raw_text'),
            'text': mb.get('text'),
        }
        rs = mb.get('retweeted_status')
        if rs:
            o['timeline']['rt'] = {'id': rs.get('id'),
                                   'user': (rs.get('user') or {}).get('screen_name'),
                                   'text': rs.get('text'),
                                   'isLongText': rs.get('isLongText')}
    # show
    try:
        h1 = {'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest',
              'Referer': f'https://m.weibo.cn/detail/{wid}'}
        r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}',
                         headers=h1, cookies=w.COOKIES, timeout=15)
        d = (r.json() or {}).get('data') or {}
        o['show'] = {
            'status': r.status_code,
            'created_at': d.get('created_at'),
            'repost_type': d.get('repost_type'),
            'isLongText': d.get('isLongText'),
            'raw_text': d.get('raw_text'),
            'text': d.get('text'),
        }
        rs = d.get('retweeted_status')
        if rs:
            o['show']['rt'] = {
                'id': rs.get('id'),
                'user': (rs.get('user') or {}).get('screen_name'),
                'created_at': rs.get('created_at'),
                'text': rs.get('text'),
                'isLongText': rs.get('isLongText'),
                'pics': [(p.get('large') or {}).get('url') for p in (rs.get('pics') or [])],
            }
    except Exception as e:
        o['show'] = {'err': str(e)}
    # pc longtext
    r2 = None
    try:
        h2 = {'User-Agent': UA, 'Referer': 'https://weibo.com/'}
        r2 = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={wid}',
                          headers=h2, cookies=w.COOKIES, timeout=15)
        d2 = r2.json()
        o['pc'] = {'status': r2.status_code, 'ok': d2.get('ok'),
                   'ltc': (d2.get('data') or {}).get('longTextContent')}
    except Exception as e:
        o['pc'] = {'err': str(e), 'raw_head': (r2.text[:200] if r2 is not None else '')}
    # extend
    try:
        r3 = requests.get(f'https://m.weibo.cn/statuses/extend?id={wid}',
                          headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=15)
        d3 = r3.json()
        o['extend'] = {'status': r3.status_code, 'ok': d3.get('ok'),
                       'ltc': (d3.get('data') or {}).get('longTextContent')}
    except Exception as e:
        o['extend'] = {'err': str(e)}
    # render page source
    try:
        r4 = requests.get(f'https://m.weibo.cn/status/{wid}?_=2',
                          headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
        html = r4.text
        o['render'] = {'status': r4.status_code, 'len': len(html),
                       'expand_count': html.count('展开全文')}
        mrd = re.search(r'var \$render_data = (\[.*?\]);', html, re.S)
        if mrd:
            j = json.loads(mrd.group(1))
            stt = (j[0] or {}).get('status') or {}
            o['render']['rd'] = {'raw_text': stt.get('raw_text'),
                                 'text': stt.get('text'),
                                 'repost_type': stt.get('repost_type')}
    except Exception as e:
        o['render'] = {'err': str(e)}
    OUT[wid] = o

fn = '/home/coordinate35/hermes_data/weibo_data/verify_3posts_20260924_1551.json'
with open(fn, 'w', encoding='utf-8') as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1)
print('SAVED', fn)
print()

for wid in IDS:
    o = OUT[wid]
    sh = o.get('show') or {}
    print('=' * 72)
    print('ID', wid, '| created_at:', sh.get('created_at'),
          '| repost_type:', sh.get('repost_type'), '| isLongText:', sh.get('isLongText'))
    print('--- show.raw_text (FULL) ---')
    print(sh.get('raw_text'))
    print('--- show.text tail ---')
    print((sh.get('text') or '')[-100:])
    pc = o.get('pc') or {}
    ltc = pc.get('ltc') or ''
    print('--- pc.ltc len', len(ltc), 'tail ---')
    print(ltc[-220:])
    ex = o.get('extend') or {}
    el = ex.get('ltc') or ''
    print('--- extend.ltc len', len(el), 'tail ---')
    print(el[-220:])
    rend = o.get('render') or {}
    rd = rend.get('rd') or {}
    print('--- render expand_count:', rend.get('expand_count'), '| rd.raw_text tail ---')
    print((rd.get('raw_text') or '')[-220:])
    print('--- rd.text tail ---')
    print((rd.get('text') or '')[-220:])
    rt = sh.get('rt')
    if rt:
        print('--- show.rt:', rt.get('id'), '|', rt.get('user'),
              '| isLongText', rt.get('isLongText'), '| created', rt.get('created_at'))
        print('rt.text head:', (rt.get('text') or '')[:150])
    tl_ = o.get('timeline') or {}
    trt = tl_.get('rt')
    if trt:
        print('--- timeline.rt:', trt.get('id'), '|', trt.get('user'))
    print()
