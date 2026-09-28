#!/usr/bin/env python3
"""评论配图页可达性检查（2026-09-28 20:31 批）: t.cn/AXWV80iA -> compic"""
import requests

H = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'}
u = 'https://photo.weibo.com/h5/comment/compic_id/1022:230597f04468cde11a6b2eff67438697666c4a'
r = requests.get(u, headers=H, timeout=25)
print('status:', r.status_code, 'len:', len(r.text), 'ctype:', r.headers.get('Content-Type'))
print('head:', r.text[:200].replace('\n', ' '))
