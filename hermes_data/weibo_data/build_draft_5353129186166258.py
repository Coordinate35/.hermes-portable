#!/usr/bin/env python3
# Build delivery draft + voice text for post 5353129186166258 (raw inserted from verify JSON).
import json

VJ = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5353129186166258.json"
DRAFT = "/home/coordinate35/hermes_data/weibo_data/delivery_20261012_0935.txt"
VOICE = "/tmp/voice_text_wb_20261012_0935.txt"

raw = json.load(open(VJ, encoding="utf-8"))["raw_text"]

header = "**@卢麒元 · 新微博 · 10-12 09:35:17 · 华为Mate XT 非凡大师**（转20 · 评4 · 赞38）"
summary = ("卢麒元附评论转发其本人 10-09「置顶文再次被限」帖：汇率讨论总是被限流，但仍需澄清要点"
           "——事关中美博弈生死局（资本流向）；油价回不去、通胀即将飞起，西大策略是逼我们撒钱（所谓拉动消费）；"
           "正确做法是以人民币汇率消化大部分输入型通胀（绝不能偷偷以通胀化债），可考虑锁死工业用电价格、间接锚定石油价格，确保产业和生活；"
           "本币升值必须精算，同时要有管控资本流向的严密措施（升值预期必须高于加息预期）。")
note = ("本条为附评论转发，转发的是其本人 10-09 21:22:36「置顶文再次被限」帖（此前已推送，不重复附全文）。"
        "经 show 接口与渲染页副本×2 核验一致、无折叠内容（展开全文/查看全文/查看更多/全文计数=0），逐字节比对 0 差异。")

draft = (f"{header}\n\n📌 总结\n{summary}\n\n📄 完整原文\n{raw}\n\n📎 注\n{note}\n\n"
         f"🎙️ 语音由 Windows TTS 生成（第1级）\nMEDIA:/tmp/weibo_voice.wav\n")
open(DRAFT, "w", encoding="utf-8").write(draft)

voice = ("卢麒元发布新微博：" + raw +
         "本条为附评论转发，转发的是其本人此前发布的《置顶文再次被限》帖，该帖已推送过。")
open(VOICE, "w", encoding="utf-8").write(voice)

print("DRAFT:", DRAFT, len(draft))
print("VOICE:", VOICE, len(voice))
