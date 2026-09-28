#!/usr/bin/env python3
"""外链核验（2026-09-28 20:31 批）：t.cn/AXWV80iA 解析 + 图片直链可达性检查"""
import requests

H = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'}
s = requests.Session()

r = s.get('http://t.cn/AXWV80iA', headers=H, allow_redirects=True, timeout=25)
print('t.cn final:', r.status_code, r.url)
print('t.cn history codes:', [h.status_code for h in r.history])
print('t.cn history locs:', [h.headers.get('Location') for h in r.history][:6])

img_url = 'https://wx1.sinaimg.cn/large/543672c7ly1ihjnihpwlvj20qp0qxjwj.jpg'
g = s.get(img_url, headers=H, stream=True, timeout=25)
print('img:', g.status_code, g.headers.get('Content-Type'), g.headers.get('Content-Length'))
g.close()
