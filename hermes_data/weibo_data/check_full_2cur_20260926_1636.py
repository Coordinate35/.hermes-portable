#!/usr/bin/env python3
"""核验 2026-09-26 16:36 轮 2 条新帖：show / pc longtext / extend / 渲染 + 时间线卡片。
IDs: 5347434471363219 (16:26:31 回复@真爱从不浪漫), 5347434534274609 (16:26:45 回复@雁过withouttrace)"""
import sys, json, re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

IDS = ['5347434471363219', '5347434534274609']
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
OUT = {}

tl = {}
try:
    url = ('https://m.weibo.cn/api/container/getIndex?uid=1245732825&type=uid'
           '&value=1245732825&containerid=1076031245732825')
    data = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=15).json()
    for c in data.get('data', {}).get('cards', []):
        if c.get('card_type') == 9:
            mb = c.get('mblog') or {}
            rsmb = mb.get('retweeted_status') or None
            tl[str(mb.get('id'))] = {
                'created_at': mb.get('created_at'), 'source': mb.get('source'),
                'isLongText': mb.get('isLongText'), 'raw_text': mb.get('raw_text'),
                'text': mb.get('text'),
                'rt': ({'id': str(rsmb.get('id')),
                        'user': (rsmb.get('user') or {}).get('screen_name'),
                        'text': rsmb.get('text')} if rsmb else None),
            }
    print('timeline cards:', len(tl))
except Exception as e:
    print('timeline failed:', e)

for wid in IDS:
    o = {}
    o['timeline'] = tl.get(wid)
    # show
    try:
        h1 = {'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest', 'Referer': f'https://m.weibo.cn/detail/{wid}'}
        r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}', headers=h1, cookies=w.COOKIES, timeout=15)
        d = (r.json() or {}).get('data') or {}
        o['show'] = {
            'status': r.status_code,
            'created_at': d.get('created_at'), 'source': d.get('source'),
            'repost_type': d.get('repost_type'), 'isLongText': d.get('isLongText'),
            'raw_text': d.get('raw_text'), 'text': d.get('text'),
            'comments_count': d.get('comments_count'), 'reposts_count': d.get('reposts_count'),
            'attitudes_count': d.get('attitudes_count'),
        }
        rs = d.get('retweeted_status')
        if rs:
            o['show.rt'] = {
                'id': str(rs.get('id')), 'user': (rs.get('user') or {}).get('screen_name'),
                'created_at': rs.get('created_at'), 'isLongText': rs.get('isLongText'),
                'raw_text': rs.get('raw_text'), 'text': rs.get('text'),
                'pics': [(p.get('large') or {}).get('url') for p in (rs.get('pics') or [])],
            }
            if rs.get('longTextContent'):
                o['show.rt']['ltc_tail'] = (rs.get('longTextContent') or '')[-300:]
    except Exception as e:
        o['show'] = {'err': str(e)}
    # pc longtext
    try:
        h2 = {'User-Agent': UA, 'Referer': 'https://weibo.com/'}
        r2 = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={wid}', headers=h2, cookies=w.COOKIES, timeout=15)
        try:
            d2 = r2.json()
            o['pc'] = {'status': r2.status_code, 'ok': d2.get('ok'),
                       'ltc': (d2.get('data') or {}).get('longTextContent')}
        except Exception:
            o['pc'] = {'status': r2.status_code, 'raw_head': r2.text[:200]}
    except Exception as e:
        o['pc'] = {'err': str(e)}
    # extend
    try:
        r3 = requests.get(f'https://m.weibo.cn/statuses/extend?id={wid}', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=15)
        d3 = r3.json()
        o['extend'] = {'status': r3.status_code, 'ok': d3.get('ok'), 'ltc': (d3.get('data') or {}).get('longTextContent')}
    except Exception as e:
        o['extend'] = {'err': str(e)}
    # render
    try:
        r4 = requests.get(f'https://m.weibo.cn/status/{wid}?_=2', headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
        html = r4.text
        o['render'] = {'status': r4.status_code, 'len': len(html), 'expand_count': html.count('展开全文')}
        mrd = re.search(r'var \$render_data = (\[.*?\]);', html, re.S)
        if mrd:
            j = json.loads(mrd.group(1))
            stt = (j[0] or {}).get('status') or {}
            o['render']['rd'] = {'raw_text': stt.get('raw_text'), 'text': stt.get('text'), 'repost_type': stt.get('repost_type')}
    except Exception as e:
        o['render'] = {'err': str(e)}
    OUT[wid] = o

fn = '/home/coordinate35/hermes_data/weibo_data/verify_2cur_20260926_1636.json'
with open(fn, 'w', encoding='utf-8') as f:
    json.dump(OUT, f, ensure_ascii=False, indent=1)
print('SAVED', fn)
print()
for wid in IDS:
    o = OUT[wid]
    sh = o.get('show') or {}
    print('=' * 72)
    print('ID', wid, '| created_at:', sh.get('created_at'), '| repost_type:', sh.get('repost_type'),
          '| isLongText:', sh.get('isLongText'), '| src:', sh.get('source'))
    print('--- show.raw_text (FULL) ---')
    print(sh.get('raw_text'))
    print('--- show.text tail ---')
    print((sh.get('text') or '')[-160:])
    rt = o.get('show.rt')
    if rt:
        print('--- show.rt:', rt.get('id'), rt.get('user'), '| isLongText', rt.get('isLongText'), '| created', rt.get('created_at'))
        print('rt.raw_text FULL:')
        print(rt.get('raw_text'))
        print('rt.text tail:', (rt.get('text') or '')[-160:])
    pc = o.get('pc') or {}
    print('--- pc.ltc len', len(pc.get('ltc') or ''), 'tail ---')
    print((pc.get('ltc') or '')[-250:])
    ex = o.get('extend') or {}
    print('--- extend.ltc len', len(ex.get('ltc') or ''), 'tail ---')
    print((ex.get('ltc') or '')[-250:])
    rend = o.get('render') or {}
    rd = rend.get('rd') or {}
    print('--- render expand_count:', rend.get('expand_count'))
    print('rd.raw_text tail:', (rd.get('raw_text') or '')[-250:])
    tlm = o.get('timeline')
    print('--- timeline raw_text tail ---')
    print(((tlm or {}).get('raw_text') or '')[-250:])
    print()
