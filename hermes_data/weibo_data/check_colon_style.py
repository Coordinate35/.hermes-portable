#!/usr/bin/env python3
"""比对 17:04 已交付 .md 中引用链的冒号/字符风格（与本次 raw 对照）。"""
p = '/home/coordinate35/.hermes/cron/output/a27ae1b5f602/2026-09-19_17-04-40.md'
s = open(p, encoding='utf-8').read()
for anchor in ['回复@迅羽', '//@卢麒元', '回复@卢师最菜弟子', '太闲了']:
    i = s.find(anchor)
    print(anchor, '->', repr(s[i:i+24]) if i >= 0 else 'NOT FOUND')
# 交付行里半角冒号统计
seg = s[s.find('📄 完整原文'):s.find('📎 注')]
print('半角冒号 count:', seg.count(':'), '| 全角冒号 count:', seg.count('：'))
