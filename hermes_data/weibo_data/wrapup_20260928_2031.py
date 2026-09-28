#!/usr/bin/env python3
"""本批收尾（2026-09-28 20:31 批）：链接缓存回写（头条视频/评论配图）＋ jobs.json 内部状态核对"""
import json
import os
import re
import subprocess
import sys

import requests

sys.path.insert(0, '/home/coordinate35/.hermes/scripts')
import weibo_monitor as w  # noqa: E402

LC = '/home/coordinate35/.hermes/skills/data-collection/weibo-monitoring/scripts/link_cache.py'


def show(wid):
    h = dict(w.HEADERS)
    h['X-Requested-With'] = 'XMLHttpRequest'
    h['Referer'] = f'https://m.weibo.cn/detail/{wid}'
    return requests.get(f'https://m.weibo.cn/statuses/show?id={wid}',
                        headers=h, cookies=w.COOKIES, timeout=20).json().get('data', {})


def store(payload):
    r = subprocess.run(['python3', LC, 'store', '-'],
                       input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True)
    out = (r.stdout or '').strip().replace('\n', ' ')
    err = (r.stderr or '').strip().replace('\n', ' ')
    print('store rc:', r.returncode, '|', out[:260], ('| ERR: ' + err[:200]) if err else '')


d = show('5348218445760068')
m = re.search(r'href="(https://weibo\.cn/sinaurl[^"]+)"', d.get('text', '') or '')
sinaurl = m.group(1) if m else ''
print('sinaurl extracted ok:', bool(sinaurl), '|', (sinaurl[:100] + '...') if sinaurl else '')

store({
    'url': 'https://m.toutiao.com/video/7690471173083169308',
    'sinaurl': sinaurl,
    'kind': 'toutiao_video',
    'title': '听听卢麒元教授怎么说？',
    'author': '有一说一',
    'date': '2026-09-28T14:36:03+08:00',
    'extra': '时长PT2M11S',
})
store({
    'url': 'https://photo.weibo.com/h5/comment/compic_id/1022:230597f04468cde11a6b2eff67438697666c4a',
    'sinaurl': 'http://t.cn/AXWV80iA',
    'kind': 'weibo_compic',
    'title': '评论配图页（@youngwe 评论附图）',
    'extra': 't.cn 302 直达；源帖 5348218546166095',
})

p = os.path.expanduser('~/.hermes/cron/jobs.json')
try:
    data = json.load(open(p, encoding='utf-8'))
    jobs = data if isinstance(data, list) else data.get('jobs', data)
    if isinstance(jobs, dict):
        jobs = list(jobs.values())
    hits = 0
    for j in jobs:
        if not isinstance(j, dict):
            continue
        le, lde, fs = j.get('last_error'), j.get('last_delivery_error'), j.get('failure_streak')
        if le or lde or (fs and fs > 0):
            hits += 1
            print('JOB-CHECK:', j.get('id') or j.get('job_id'), '|', j.get('name'),
                  '| last_error=', str(le)[:120], '| last_delivery_error=', str(lde)[:80],
                  '| failure_streak=', fs)
    print('jobs.json scanned:', len(jobs), 'jobs; anomaly hits:', hits)
except Exception as e:
    print('jobs.json read fail:', e)
