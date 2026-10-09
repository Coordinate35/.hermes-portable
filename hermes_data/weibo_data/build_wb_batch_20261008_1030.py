#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build per-post verification drafts + final batch delivery for 2026-10-08 10:30 weibo round.
原文块一律从 wb_verify_<id>.json 的 raw_text 直接读取，杜绝转录笔误。"""
import json
import os

BASE = os.path.expanduser("~/hermes_data/weibo_data")

posts = [
    {
        "id": "5351689555283007",
        "time": "10-08 10:14:42",
        "counts": "转77 · 评15 · 赞151",
        "summary": "卢麒元回复@民兵连菜市场阿姨：坚持其港府投资机构发行稳定币的建议——已提出超过五年、一直遭到系统性屏蔽，港币联汇问题也一直噤若寒蝉；称该建议才真正是香港大型金融基建的重要基石。",
    },
    {
        "id": "5351693232899262",
        "time": "10-08 10:29:18",
        "counts": "转3 · 评2 · 赞4",
        "summary": "卢麒元回复@MCH2017（问「为何阻力这么大」）：真诚希望香港金融不再是华尔街的鞋垫，能成为祖国最锐利的金融工具、成为可怜港人的谋生依托。",
    },
    {
        "id": "5351693445235128",
        "time": "10-08 10:30:09",
        "counts": "转0 · 评0 · 赞0",
        "summary": "卢麒元回复@我子睿（网友留言建议其试服玉屏风颗粒调理易感冒），以[握手]致意。",
    },
]

HEADER = "**@卢麒元 · 新微博 · {time} · 华为Mate XT 非凡大师**（{counts}）"

blocks = []
for p in posts:
    with open(f"{BASE}/wb_verify_{p['id']}.json", encoding="utf-8") as f:
        vj = json.load(f)
    b = vj.get("raw_text") or (vj.get("text_stripped") or "").rstrip()
    blocks.append(b)
    t = (f"{HEADER.format(time=p['time'], counts=p['counts'])}\n\n"
         f"📌 总结\n{p['summary']}\n\n"
         f"📄 完整原文\n{b}\n\n"
         f"📎 注\n（占位）\n")
    with open(f"{BASE}/draft_p_{p['id']}.md", "w", encoding="utf-8") as f:
        f.write(t)

note = ("三条均系回复类帖：①10:14:42 回复@民兵连菜市场阿姨；②10:29:18 回复@MCH2017（「为何阻力这么大」）；"
        "③10:30:09 回复@我子睿。链引段均按微博端原样止点照发——①、③链引其本人 09:59:34 稳定币建议帖段"
        "（完整版此前已推送），止于「…准政府发行的超级稳定币（全球穿透式交易的有效」；"
        "②链引①帖回复段（完整）及@民兵连菜市场阿姨评论段，止于「…以国债黄金为底，构」（词中截断）。"
        "三条帖内转发卡片均为@财联社APP「中国央行连续第23个月增持黄金」帖（10-07 10:14:41，此前已推送），"
        "不重复附全文。")

final = ""
for i, p in enumerate(posts):
    final += (f"{HEADER.format(time=p['time'], counts=p['counts'])}\n\n"
              f"📌 总结\n{p['summary']}\n\n"
              f"📄 完整原文\n{blocks[i]}\n\n")
final += f"📎 注\n{note}\n"

# 断言：每条原文块与权威 JSON 逐字节一致，且完整包含于最终稿
for i, p in enumerate(posts):
    with open(f"{BASE}/wb_verify_{p['id']}.json", encoding="utf-8") as f:
        vj = json.load(f)
    assert blocks[i] == (vj.get("raw_text") or (vj.get("text_stripped") or "").rstrip())
    assert blocks[i] in final

with open(f"{BASE}/final_delivery_20261008_1030.md", "w", encoding="utf-8") as f:
    f.write(final)

print("OK")
print("blocks:", [len(b) for b in blocks])
print("final_len:", len(final))
