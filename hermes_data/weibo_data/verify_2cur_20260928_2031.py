#!/usr/bin/env python3
"""本批 2 帖（2026-09-28 20:31 批）show 端点核验 + 交付文本逐字节校验。
B=5348218445760068 (20:21:45 网页链接) | A=5348218546166095 (20:22:09 回复@youngwe)
"""
import re
import sys

import requests

sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import weibo_monitor as w  # noqa: E402


def strip_html(t):
    return re.sub(r'<[^>]+>', '', t or '')


def show(wid):
    h = dict(w.HEADERS)
    h['X-Requested-With'] = 'XMLHttpRequest'
    h['Referer'] = f'https://m.weibo.cn/detail/{wid}'
    r = requests.get(f'https://m.weibo.cn/statuses/show?id={wid}',
                     headers=h, cookies=w.COOKIES, timeout=20)
    return r.json()


B = '5348218445760068'
A = '5348218546166095'

data = {}
for wid, tag in ((B, 'B-20:21:45'), (A, 'A-20:22:09')):
    j = show(wid)
    d = j.get('data', {})
    data[wid] = d
    print(f'===== {tag} id={d.get("id")} repost_type={d.get("repost_type")}')
    print('raw_text:', repr(d.get('raw_text')))
    print('strip_text:', repr(strip_html(d.get('text', ''))))
    rs = d.get('retweeted_status')
    if rs:
        ru = rs.get('user') or {}
        print('card: id=', rs.get('id'), 'bid=', rs.get('bid'),
              'user=', ru.get('screen_name'), 'created_at=', rs.get('created_at'),
              'text=', repr(strip_html(rs.get('text', ''))[:90]))
    else:
        print('card: none')

print()
print('========== 交付文本校验 ==========')
rawA = (data[A].get('raw_text') or '')
expA = '回复@youngwe:[鲜花][鲜花][鲜花]//@youngwe:《卢麒元：启动水循环建设》 http://t.cn/AXWV80iA'
print('A raw_text == 预期字面:', rawA.rstrip() == expA.rstrip())
delA = rawA.rstrip().replace('http://t.cn/AXWV80iA', '评论配图')
print('A 交付块:', repr(delA))
print('A 交付块 == 基准替换后:', delA == expA.replace('http://t.cn/AXWV80iA', '评论配图'))

txtB = strip_html(data[B].get('text', ''))
print('B text 原始:', repr(txtB))
delB = txtB.rstrip()
print('B 交付块:', repr(delB), '== "网页链接":', delB == '网页链接')
