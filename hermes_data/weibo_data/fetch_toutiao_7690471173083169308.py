#!/usr/bin/env python3
"""抓取头条视频页核验信息（2026-09-28 20:31 批，post B 5348218445760068 -> video 7690471173083169308）"""
import json
import re

import requests

URL = 'https://m.toutiao.com/video/7690471173083169308/'
H = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'}

r = requests.get(URL, headers=H, timeout=25)
print('HTTP:', r.status_code, 'len:', len(r.text))
html = r.text

m = re.search(r'<title>(.*?)</title>', html, re.S)
print('TITLE:', m.group(1).strip() if m else None)

m = re.search(r'<meta[^>]+(?:property|name)="og:title"[^>]*>', html)
if m:
    mm = re.search(r'content="([^"]*)"', m.group(0))
    print('OG_TITLE:', mm.group(1) if mm else m.group(0)[:200])
else:
    print('OG_TITLE: not found')
    mm = re.search(r'"title":"([^"]{4,80})"', html)
    print('FALLBACK_TITLE:', mm.group(1) if mm else None)

m = re.search(r'class="author-info-name"[^>]*>(.*?)</', html, re.S)
print('AUTHOR:', m.group(1).strip() if m else None)

m = re.search(r'class="author-info-desc"[^>]*>(.*?)</', html, re.S)
print('AUTHOR_DESC:', m.group(1).strip() if m else None)

blocks = list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S))
print('LDJSON blocks:', len(blocks))
for i, m in enumerate(blocks):
    try:
        j = json.loads(m.group(1))
    except Exception as e:
        print(f'LDJSON#{i} parse-fail: {e}')
        continue
    items = j if isinstance(j, list) else (j.get('@graph') if isinstance(j, dict) and '@graph' in j else [j])
    for it in items:
        if isinstance(it, dict) and it.get('@type') == 'VideoObject':
            out = {k: it.get(k) for k in ('name', 'uploadDate', 'duration', 'author')}
            print('VIDEOOBJECT:', json.dumps(out, ensure_ascii=False))
