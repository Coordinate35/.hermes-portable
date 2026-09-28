#!/usr/bin/env python3
"""拟交付稿 delivery_20260928_2031.txt 的「📄 完整原文」块与 show 权威文本逐字节校验"""
import re
import sys

import requests

sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import weibo_monitor as w  # noqa: E402

DRAFT = '/home/coordinate35/hermes_data/weibo_data/delivery_20260928_2031.txt'
draft = open(DRAFT, encoding='utf-8').read()


def show(wid):
    h = dict(w.HEADERS)
    h['X-Requested-With'] = 'XMLHttpRequest'
    h['Referer'] = f'https://m.weibo.cn/detail/{wid}'
    return requests.get(f'https://m.weibo.cn/statuses/show?id={wid}',
                        headers=h, cookies=w.COOKIES, timeout=20).json().get('data', {})


blocks = re.findall(r'📄 完整原文\n(.+?)\n\n', draft, re.S)
print('blocks 数量:', len(blocks))
for i, b in enumerate(blocks):
    print(f'block{i}:', repr(b))

dB, dA = show('5348218445760068'), show('5348218546166095')
rawB = re.sub(r'<[^>]+>', '', dB.get('text', '') or '').rstrip()
rawA = (dA.get('raw_text') or '').rstrip()
print('A raw_text:', repr(rawA))
expA = rawA.replace('http://t.cn/AXWV80iA', '评论配图')

okB = len(blocks) >= 1 and blocks[0] == rawB
okA = len(blocks) >= 2 and blocks[1] == expA
print('B 块 == text(rstrip):', okB, '| 期望:', repr(rawB))
print('A 块 == raw_text(链替换显示文案):', okA, '| 期望:', repr(expA))
if not okB and len(blocks) >= 1:
    print('B diff:', repr(blocks[0]), 'vs', repr(rawB))
if not okA and len(blocks) >= 2:
    print('A diff:', repr(blocks[1]), 'vs', repr(expA))
print('RESULT:', 'ALL-OK' if (okB and okA) else 'MISMATCH')
