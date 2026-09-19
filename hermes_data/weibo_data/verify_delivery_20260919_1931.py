#!/usr/bin/env python3
"""交付前逐字核验：raw_full 的标点/字符计数与 repr（半角冒号 vs 全角冒号等）。"""
import json
d = json.load(open('/tmp/wb_check2.json'))
checks = ['[鲜花]', '[作揖]', '[祈祷]', '[握手]', '[打call]', '//', '汗流浃背', '讳莫如深', '殖阀藩', '辨证', '鑫昰晟']
for k in ['5344943035909706', '5344943112454432']:
    s = d[k]['raw_full']
    print('=' * 30)
    print('ID:', k, 'len:', len(s))
    colon = sorted(set(ch for ch in s if ch in ':：'))
    print('colon codes:', [hex(ord(c)) for c in colon])
    for t in checks:
        print(f'  {t}: {s.count(t)}')
    print('REPR_HEAD:', repr(s[:36]))
    print('REPR_MID_1:', repr(s[s.find('回复@迅羽')-2:s.find('回复@迅羽')+26]))
    print('REPR_TAIL:', repr(s[-30:]))
