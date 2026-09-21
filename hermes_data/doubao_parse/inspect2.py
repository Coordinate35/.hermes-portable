#!/usr/bin/env python3
"""Find the script containing the data and show its raw beginning."""
import re

html = open('/tmp/doubao_thread.html', encoding='utf-8', errors='replace').read()

pos = html.find('message_snapshot')
# find enclosing script start
s_start = html.rfind('<script', 0, pos)
s_end = html.find('</script>', pos)
print("script range:", s_start, s_end)
seg = html[s_start:s_end]
print("script tag head:", seg[:200])
print("script content len:", len(seg))

# show raw text from 500 chars before message_snapshot
i = pos - s_start
raw_before = seg[max(0, i-500):i+100]
print("=== RAW before/around (no repr) ===")
print(raw_before)

# check for JSON.parse / push / atob patterns
for kw in ['JSON.parse', 'push(', 'atob', '__DATA', 'window.', 'self.', 'application/json', 'RENDER', 'loadingData', 'initData', 'threadShare']:
    c = seg.count(kw)
    print(kw, '->', c)

# find the start of the embedded object: look for '{"' or escaped equivalents before pos
# search backwards for patterns
for pat in ['\\\\{\\\\"', '{\\"', '\\{"', '{"', '\\u007B']:
    idx = seg.rfind(pat, 0, i)
    print(repr(pat), '->', idx)
