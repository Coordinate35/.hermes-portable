#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build draft + voice text for weibo round 2026-10-09 10:43 (id 5352059115406034).
原文块从 wb_verify_<id>.json 的 raw_text 直接读取，杜绝转录笔误。"""
import json
import os

BASE = os.path.expanduser("~/hermes_data/weibo_data")
WID = "5352059115406034"

with open(f"{BASE}/wb_verify_{WID}.json", encoding="utf-8") as f:
    vj = json.load(f)
raw = vj.get("raw_text") or (vj.get("text_stripped") or "").rstrip()
assert vj.get("pc_longtext") == raw, "raw_text vs pc_longtext mismatch"
assert raw.endswith("港币联汇问题也") and "[祈祷]" in raw and raw.count("[祈祷]") == 2

header = "**@卢麒元 · 新微博 · 10-09 10:43:11 · 华为Mate XT 非凡大师**（转15 · 评5 · 赞28）"

summary = ("卢麒元回复@果果然D：以「水缸漏水」为喻谈资本流向——香港本应成为东大入水口、现在成了东大的滴漏，"
           "北水南调然后变成了西调；称要害仍然是汇率，「汇率升值预期不能平抑利率预期，就必须开启强制结汇」，"
           "「第五爻了，要出事了，必须出手了」。")

note = ("本条为回复链帖：回复@果果然D（评论「信念心念的力量惊天动地！」）。"
        "链引其本人 10-08 10:29:18 帖（回复@MCH2017）与 10-08 10:14:42 帖（回复@民兵连菜市场阿姨）两个回复段，"
        "完整版此前均已推送、不重复附全文；全链按微博端原样止于「…港币联汇问题也」（词中截断，勿延伸）。"
        "帖内转发卡片为@财联社APP「中国央行连续第23个月增持黄金」帖（10-07 10:14:41，此前已推送），不重复附全文。")

draft = f"{header}\n\n📌 总结\n{summary}\n\n📄 完整原文\n{raw}\n\n📎 注\n{note}\n"

with open(f"{BASE}/draft_{WID}.md", "w", encoding="utf-8") as f:
    f.write(draft)

voice = ("卢麒元发布新微博。回复果果然D：谢谢啊，一个祈祷。小时候家里用过水缸。水缸漏了，一担担地挑水是没有意义的。"
         "我一再强调资本流向，说得就是水漏走了。香港本应成为东大入水口，现在成了东大的滴漏。"
         "北水南调，然后变成了西调。要害仍然是汇率，汇率升值预期不能平抑利率预期，就必须开启强制结汇。"
         "第五爻了，要出事了，必须出手了。转发果果然D：信念心念的力量惊天动地！"
         "转发卢麒元：回复MCH二零一七：真诚地希望，香港金融不再是华尔街的鞋垫；热切地盼望，香港金融能成为祖国最锐利的金融工具。"
         "当然，也恳切地希望，香港金融能成为可怜港人的谋生依托，一个祈祷。转发MCH二零一七：为何阻力这么大。"
         "转发卢麒元：回复民兵连菜市场阿姨：是的。建议已经超过五年了。一直遭到系统性的屏蔽。港币联汇问题也。"
         "本条为回复链帖，链内所引其本人两帖段及帖内转发卡片此前均已推送，不再重复附全文。")

with open("/tmp/voice_text_wb_20261009_1043.txt", "w", encoding="utf-8") as f:
    f.write(voice)

assert raw in draft
for s in ["卢麒元发布新微博。", "回复果果然D：", "谢谢啊，一个祈祷。", "必须出手了。",
          "转发果果然D：信念心念的力量惊天动地！", "转发卢麒元：回复MCH二零一七：",
          "谋生依托，一个祈祷。", "转发MCH二零一七：为何阻力这么大。",
          "转发卢麒元：回复民兵连菜市场阿姨：", "港币联汇问题也。", "不再重复附全文。"]:
    assert s in voice, f"voice missing: {s}"
assert voice.endswith("不再重复附全文。")

print("OK")
print("raw_len:", len(raw))
print("draft_len:", len(draft))
print("voice_len:", len(voice))
print("=== VOICE ===")
print(voice)
