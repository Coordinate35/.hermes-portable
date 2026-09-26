#!/usr/bin/env python3
"""核验拟交付稿 2 条帖「📄 完整原文」块 vs show raw_text 逐字节 diff + 交叉源核验 + 口播稿检查。"""
import sys, json, re, difflib
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')

base = '/home/coordinate35/hermes_data/weibo_data/'
vj = json.load(open(base + 'verify_2cur_20260926_1636.json', encoding='utf-8'))
draft = open('/tmp/weibo_delivery_draft_20260926_1636.txt', encoding='utf-8').read()
voice = open('/tmp/voice_text_wb_20260926_1636.txt', encoding='utf-8').read()

ids = ['5347434471363219', '5347434534274609']
blocks = re.findall(r'📄 完整原文\n(.*?)(?=\n\n📎 注|\n\n\*\*@)', draft, re.S)
print('blocks found:', len(blocks))
assert len(blocks) == 2, 'expected 2 blocks'

def html2text(h):
    h = re.sub(r'<img[^>]*alt="(\[[^"]*?\])"[^>]*/?>', r'\1', h or '')
    h = re.sub(r'<a [^>]*>([^<]*)</a>', r'\1', h or '')
    h = re.sub(r'<[^>]+>', '', h or '')
    return h

ok_all = True
for wid, blk in zip(ids, blocks):
    o = vj[wid]
    raw = (o['show'].get('raw_text') or '')
    print('=' * 72)
    print('ID', wid)
    print('draft block len:', len(blk), '| raw len:', len(raw))
    if blk == raw:
        print('BYTE-EQUAL: PASS')
    else:
        ok_all = False
        print('BYTE-EQUAL: FAIL')
        for s in difflib.unified_diff([raw], [blk], 'raw', 'draft', lineterm=''):
            print(s)
        for i, (a, b) in enumerate(zip(raw, blk)):
            if a != b:
                print('first diff at', i, repr(raw[max(0, i - 25):i + 25]), '||', repr(blk[max(0, i - 25):i + 25]))
                break
    pc = (o.get('pc') or {}).get('ltc') or ''
    print('pc == raw:', pc == raw, '| pc len:', len(pc))
    ex = html2text((o.get('extend') or {}).get('ltc') or '')
    print('extend(strip)==raw:', ex == raw)
    tx = html2text(o['show'].get('text') or '')
    print('show.text(strip)==raw:', tx == raw)
    print('raw tail repr:', repr(raw[-12:]), '| raw head repr:', repr(raw[:18]))
    sh = o['show']
    print('counts: repost', sh.get('reposts_count'), 'comment', sh.get('comments_count'), 'like', sh.get('attitudes_count'))
    rt = o.get('show.rt') or {}
    rtx = html2text(rt.get('text') or '')
    print('rt:', rt.get('id'), rt.get('user'), '| pics:', len(rt.get('pics') or []), '| rt text:', repr(rtx))

print('=' * 72)
# voice checks
req = ['微博播报', '都是回复网友的帖子', '真爱从不浪漫', '一个祈祷', '五个赞', '五朵鲜花', '一路劳顿', '下长安',
       '雁过withouttrace', '一朵鲜花', '抵抗力', '尚志践形']
for s in req:
    print('voice has', repr(s), ':', s in voice)
for s in ['[', ']', '@', '//']:
    print('voice excludes', repr(s), ':', s not in voice)
print('voice len:', len(voice))
print('ALL_OK:', ok_all)
