#!/usr/bin/env python3
"""Inspect raw HTML around message_snapshot to understand encoding layers."""
import re

html = open('/tmp/doubao_thread.html', encoding='utf-8', errors='replace').read()
print("HTML total len:", len(html))

# find occurrences
for m in re.finditer('message_snapshot', html):
    i = m.start()
    print("occurrence at", i)
    print("CTX BEFORE:", repr(html[max(0,i-200):i]))
    print("CTX AFTER:", repr(html[i:i+300]))
    print('---')
    break

# find script tags count
print("script tags:", len(re.findall(r'<script', html)))

# look for the beginning of the big JSON - search for 'share_info' or 'shareItem'
for kw in ['share_info', 'shareInfo', 'share_data', 'shareData', '"share"', 'og:title', 'og:description']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), html)][:5]
    print(kw, "->", idxs)
