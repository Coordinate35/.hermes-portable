#!/usr/bin/env python3
"""最终核验 2026-09-24 15:51 轮：
1) 交付稿 3 个「完整原文」块 vs show raw_text 逐字节 diff；
2) pc longtext / extend(归一化) 交叉核验；
3) 渲染页 ?_=2 / ?_=3 双副本：展开全文=0 + 尾部片段目检；
4) 口播稿 token 计数核验。
"""
import sys
import json
import re
sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import requests
import weibo_monitor as w

JJ = '/home/coordinate35/hermes_data/weibo_data/verify_3posts_20260924_1551.json'
DD = '/home/coordinate35/hermes_data/weibo_data/delivery_20260924_1551.txt'
VT = '/tmp/voice_text_wb_20260924_1551.txt'
IDS = ['5346699084303732', '5346699965104242', '5346700325816668']
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
data = json.load(open(JJ, encoding='utf-8'))
fails = []

# 1) delivery blocks vs raw
dl = open(DD, encoding='utf-8').read()
blocks = re.findall(r'📄 完整原文\n(.+?)(?:\n\n)', dl)
print('blocks found:', len(blocks), '(expect 3)')
if len(blocks) != 3:
    fails.append('block count')
for i, wid in enumerate(IDS):
    raw = data[wid]['show']['raw_text']
    got = blocks[i] if i < len(blocks) else None
    if got == raw:
        print(f'[diff] {wid}: IDENTICAL (len {len(raw)})')
    else:
        fails.append(f'diff {wid}')
        if got is None:
            print(f'[diff] {wid}: BLOCK MISSING')
        else:
            print(f'[diff] {wid}: DIFF len got={len(got)} raw={len(raw)}')
            for j in range(min(len(got), len(raw))):
                if got[j] != raw[j]:
                    print('  at', j, '|got:', repr(got[max(0, j-18):j+18]),
                          '|raw:', repr(raw[max(0, j-18):j+18]))
                    break
            else:
                print('  prefix equal; lengths differ')

# 2) pc / extend cross-check
def norm_ext(s):
    s = re.sub(r'<span class="url-icon"><img alt="([^"]*)"[^>]*></span>', r'\1', s)
    s = re.sub(r"<a href='[^']*'>([^<]*)</a>", r'\1', s)
    return s

for wid in IDS:
    raw = data[wid]['show']['raw_text']
    pc = (data[wid].get('pc') or {}).get('ltc') or ''
    ex = (data[wid].get('extend') or {}).get('ltc') or ''
    nx = norm_ext(ex)
    pcok = (pc == raw)
    exok = (nx == raw)
    print(f'[cross] {wid}: pc {"==" if pcok else "!="} raw; extend-norm {"==" if exok else "!="} raw')
    if not pcok:
        fails.append(f'pc {wid}')
        for j in range(min(len(pc), len(raw))):
            if pc[j] != raw[j]:
                print('   pc diff at', j, repr(pc[max(0, j-18):j+18]), '|', repr(raw[max(0, j-18):j+18]))
                break
    if not exok:
        fails.append(f'extend {wid}')
        for j in range(min(len(nx), len(raw))):
            if nx[j] != raw[j]:
                print('   ext diff at', j, repr(nx[max(0, j-18):j+18]), '|', repr(raw[max(0, j-18):j+18]))
                break

# 3) render double copies
TAIL = {'5346699084303732': '期待老师对后续形势的看法',
        '5346699965104242': '期待老师对后续形势的看法',
        '5346700325816668': '不花眼不迷路'}
for wid in IDS:
    for q in ('2', '3'):
        try:
            r = requests.get(f'https://m.weibo.cn/status/{wid}?_={q}',
                             headers={'User-Agent': UA}, cookies=w.COOKIES, timeout=20)
            html = r.text
            ec = html.count('展开全文')
            pos = html.rfind(TAIL[wid])
            snippet = html[pos:pos+300].replace('\n', ' ') if pos >= 0 else '(tail not found)'
            print(f'[render] {wid} ?_={q}: status={r.status_code} len={len(html)} expand={ec} rfind={pos}')
            print('   snippet:', snippet[:290])
            if r.status_code != 200 or ec != 0 or pos < 0:
                fails.append(f'render {wid} q{q}')
        except Exception as e:
            fails.append(f'render {wid} q{q}')
            print(f'[render] {wid} ?_={q}: ERR', e)

# 4) voice checks
vt = open(VT, encoding='utf-8').read()
checks = [('尚德', 0), ('尚志', 3), ('一个祈祷', 6), ('两个嘻嘻', 2), ('三个作揖', 1),
          ('三支蜡烛', 1), ('唐山十二度', 2), ('万里长城万里长', 2)]
for k, exp in checks:
    got = vt.count(k)
    print(f'[voice] {k}: {got} (expect {exp})', 'OK' if got == exp else 'MISMATCH')
    if got != exp:
        fails.append(f'voice {k}')

print()
print('RESULT:', 'ALL PASS' if not fails else f'FAILS: {fails}')
