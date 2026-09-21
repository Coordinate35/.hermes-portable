#!/usr/bin/env python3
"""List all URLs in the payload."""
import json, re

pay = json.load(open('/home/coordinate35/hermes_data/doubao_parse/share_payload.json', encoding='utf-8'))
s = json.dumps(pay, ensure_ascii=False)

urls = sorted(set(re.findall(r'https?://[^\s"\'\\<>\)\]]+', s)))
print(f"total unique urls: {len(urls)}")
for u in urls:
    print(u)
