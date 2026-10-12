#!/usr/bin/env python3
# Build delivery draft + voice text for post 5353135330826654 (raw inserted from verify JSON).
import json

VJ = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5353135330826654.json"
DRAFT = "/home/coordinate35/hermes_data/weibo_data/delivery_20261012_1001.txt"
VOICE = "/tmp/voice_text_wb_20261012_1001.txt"

vj = json.load(open(VJ, encoding="utf-8"))
raw = vj["raw_text"]
pc = vj.get("pc_longtext") or ""

print("raw_len:", len(raw))
print("raw_tail:", repr(raw[-30:]))
print("pc_tail:", repr(pc[-30:]))
print("has_amp:", "&" in raw)
print("raw==pc_longtext:", raw == pc)

header = "**@卢麒元 · 新微博 · 10-12 09:59:42 · 华为Mate XT 非凡大师**（转4 · 评1 · 赞9）"
summary = ("卢麒元回复@北斗星空2008：请提供算法，而不是留声机式的看法；是否减持美债不算大问题，"
           "真正要命的是巨额的外挂外汇——危机前的窗口期很短了，外汇该回归了，给国家留下骨血。"
           "链含对方评论段与其本人今日 09:35 汇率帖段（此前已推送）。")
note = ("① 本条为回复链帖：新回复段 → //@北斗星空2008 评论段 → //@卢麒元 引其本人今日 09:35:17 汇率帖段（该帖今晨已推送，不重复附全文）。\n"
        "② 帖内转发卡片为其本人 10-09 21:22:36「置顶文再次被限」帖（此前已推送）；不并入正文。\n"
        "③ 微博端原样止于「…间接」（词中截断），照发未延伸；经三源核验一致（show＝pc longtext＝渲染副本×2）、无折叠内容（展开全文/查看全文/查看更多/全文计数=0），逐字节比对 0 差异。")

draft = (f"{header}\n\n📌 总结\n{summary}\n\n📄 完整原文\n{raw}\n\n📎 注\n{note}\n\n"
         f"🎙️ 语音由 Windows TTS 生成（第1级）\nMEDIA:/tmp/weibo_voice.wav\n")
open(DRAFT, "w", encoding="utf-8").write(draft)

voice = ("卢麒元发布新微博。"
         "回复北斗星空二零零八：请提供算法，而不是留声机式的看法。是否减持美债，不算是大问题。真正要命的问题，是巨额的外挂外汇。危机前的窗口期很短了，外汇该回归了，给国家留下骨血。一个祈祷。"
         "转发自北斗星空二零零八：不外乎操纵汇率，还要抛掉美债，两个矛盾的做法。没有充分外汇储备汇率会一落千丈，不以人的意志为转移，借此话题博流量容易误导大众。"
         "转发自卢麒元：关于汇率的讨论，总是被限流。然而，我仍然需要将要点澄清。因为，事关中美博弈的生死局（资本流向）。油价回不去了，通胀即将飞起，西大的策略是逼我们撒钱（所谓拉动消费）。我们正确的做法是，以人民币汇率消化大部分输入型通胀（绝不能偷偷以通胀化债）。人民币汇率可以考虑锁死工业用电价格，间接。"
         "本条为回复链帖；链中所引卢麒元本人帖文与帖内转发卡片均已推送过。")
open(VOICE, "w", encoding="utf-8").write(voice)

print("DRAFT:", DRAFT, len(draft))
print("VOICE:", VOICE, len(voice))
print("---- DRAFT ----")
print(draft)
print("---- VOICE ----")
print(voice)
