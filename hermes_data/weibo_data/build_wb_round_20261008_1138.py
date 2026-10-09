#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build draft + voice text for weibo round 2026-10-08 11:38 (id 5351710661018889).
原文块从 wb_verify_<id>.json 的 raw_text 直接读取，杜绝转录笔误。"""
import json
import os

BASE = os.path.expanduser("~/hermes_data/weibo_data")
WID = "5351710661018889"

with open(f"{BASE}/wb_verify_{WID}.json", encoding="utf-8") as f:
    vj = json.load(f)
raw = vj.get("raw_text") or (vj.get("text_stripped") or "").rstrip()

header = "**@卢麒元 · 新微博 · 10-08 11:38:34 · 华为Mate XT 非凡大师**（转4 · 评0 · 赞24）"

summary = ("卢麒元回复@娜美好世界（对方留言称其为恩师，感念所授「正心以中、以无间入有隙、三断、孟子、韩昌黎、投资学、资本论、通论」等）："
           "称「你们懂我，是我坚持的最大动力」；自述一直被特定圈层污名化、被特定场域挤压和排斥——"
           "「我不介意做令狐冲，却很难笑傲江湖」。")

note = ("本条为回复类帖：回复@娜美好世界。链条＝对方留言段（称其为恩师，感念所授）＋其本人今日 11:24:17 帖段（回复@喜欢躺平的大国渔夫）"
        "＋其本人今日 10:53:31 帖段（回复@ALENNA62920，论货币贬值与借债）——两段完整版此前均已推送；"
        "全链按微博端原样止于「…美头部（财政部」（词中截断），不延伸。"
        "帖内转发卡片为@财联社APP「中国央行连续第23个月增持黄金」帖（10-07 10:14:41，此前已推送），不重复附全文。")

draft = (f"{header}\n\n📌 总结\n{summary}\n\n📄 完整原文\n{raw}\n\n📎 注\n{note}\n")

with open(f"{BASE}/draft_{WID}.md", "w", encoding="utf-8") as f:
    f.write(draft)

voice = ("卢麒元发布新微博。回复娜美好世界：谢谢你们，一个祈祷。你们懂我，是我坚持的最大动力。"
         "我一直被特定的圈层污名化，被特定的场域挤压和排斥。我不介意做令狐冲，却很难笑傲江湖，一朵鲜花，一个作揖。"
         "转发娜美好世界：在我心里您是恩师，教我正心以中，以无间入有隙，三断，孟子，韩昌黎，投资学，资本论，通论等等。"
         "转发卢麒元：回复喜欢躺平的大国渔夫：什么家都不是。孟子云：天下有道，以道殉身，天下无道，以身殉道。"
         "我等不过是愚忠的民夫而已，一个祈祷。转发喜欢躺平的大国渔夫：元宝评价老师是一流的金融战略家。"
         "转发卢麒元：回复ALENNA六二九二零：如果，你知道，一种货币会剧烈贬值；那么，最优选择，就是拼命地去借债。"
         "美头部（财政部。")

with open("/tmp/voice_text_wb_20261008_1138.txt", "w", encoding="utf-8") as f:
    f.write(voice)

# 断言：草稿包含权威原文；口播稿覆盖全链条要点、止点正确
assert raw in draft
for s in ["卢麒元发布新微博。", "回复娜美好世界：", "谢谢你们，一个祈祷。",
          "笑傲江湖，一朵鲜花，一个作揖。", "转发娜美好世界：", "通论等等。",
          "转发卢麒元：回复喜欢躺平的大国渔夫：", "民夫而已，一个祈祷。",
          "转发喜欢躺平的大国渔夫：", "转发卢麒元：回复ALENNA六二九二零：",
          "就是拼命地去借债。"]:
    assert s in voice, f"voice missing: {s}"
assert voice.endswith("美头部（财政部。")

print("OK")
print("raw_len:", len(raw))
print("draft_len:", len(draft))
print("voice_len:", len(voice))
