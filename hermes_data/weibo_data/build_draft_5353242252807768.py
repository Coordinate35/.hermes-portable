#!/usr/bin/env python3
# Build delivery draft + voice text for post 5353242252807768 (raw inserted from verify JSON).
import json

VJ = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5353242252807768.json"
DRAFT = "/home/coordinate35/hermes_data/weibo_data/delivery_20261012_1706.txt"
VOICE = "/tmp/voice_text_wb_20261012_1706.txt"

vj = json.load(open(VJ, encoding="utf-8"))
raw = vj["raw_text"]
pc = vj.get("pc_longtext") or ""

print("raw_len:", len(raw))
print("raw_tail:", repr(raw[-30:]))
print("pc_tail:", repr(pc[-30:]))
print("has_amp:", "&" in raw)
print("raw==pc_longtext:", raw == pc)

header = "**@卢麒元 · 新微博 · 10-12 17:04:34 · 华为Mate XT 非凡大师**（转13 · 评1 · 赞19）"
summary = ("卢麒元回复@一束光爱：北宋亡了，很多人在帮着徽钦做解释；甚至仍然将司马光和三苏捧上神坛"
           "——责难范仲淹、批评王安石、偏颇岳飞都不难，然而恰恰是那个时代最牛的知识分子毁掉了他们的时代；"
           "悲催的是，金人和蒙古人会善待他们的子孙吗？链含对方评论段与其本人今日 09:35 汇率帖段（此前已推送）。")
note = ("① 本条为回复链帖：新回复段 → //@一束光爱 评论段 → //@卢麒元 引其本人今日 09:35:17 汇率帖段（该帖今晨已推送，不重复附全文）。\n"
        "② 帖内转发卡片为其本人 10-09 21:22:36「置顶文再次被限」帖（此前已推送）；不并入正文。\n"
        "③ 微博端原样止于「…间接」（词中截断），照发未延伸；经三源核验一致（show＝pc longtext＝渲染副本×2）、无折叠内容（展开全文/查看全文/查看更多/全文计数=0），逐字节比对 0 差异。")

draft = (f"{header}\n\n📌 总结\n{summary}\n\n📄 完整原文\n{raw}\n\n📎 注\n{note}\n\n"
         f"🎙️ 语音由 Windows TTS 生成（第1级）\nMEDIA:/tmp/weibo_voice.wav\n")
open(DRAFT, "w", encoding="utf-8").write(draft)

voice = ("卢麒元发布新微博。"
         "回复一束光爱：北宋亡了，很多人在帮着徽钦做解释。甚至，仍然将司马光和三苏捧上神坛。责难范仲淹当然很时髦，批评王安石更是容易的，偏颇岳飞也不难。然而，恰恰是那个时代的最牛的知识分子毁掉了他们的时代。悲催的是，金人和蒙古人会善待他们的子孙吗？一点儿意思都没有！"
         "转发自一束光爱：能感受到你内心很深的家国关切，担忧国家财富流失、经济下行，希望找到一把可以激活经济、守住国家财富的钥匙，不愿看到多年积累的发展成果被外部力量收割。只是现代金融体系环环相扣，牵一发而动全身，很多政策取舍，都要在汇率、通胀、外贸、民生之间艰难寻找平衡，很难找到单一的万能解法。"
         "转发自卢麒元：关于汇率的讨论，总是被限流。然而，我仍然需要将要点澄清。因为，事关中美博弈的生死局（资本流向）。油价回不去了，通胀即将飞起，西大的策略是逼我们撒钱（所谓拉动消费）。我们正确的做法是，以人民币汇率消化大部分输入型通胀（绝不能偷偷以通胀化债）。人民币汇率可以考虑锁死工业用电价格，间接。"
         "本条为回复链帖；链中所引卢麒元本人帖文与帖内转发卡片均已推送过。")
open(VOICE, "w", encoding="utf-8").write(voice)

print("DRAFT:", DRAFT, len(draft))
print("VOICE:", VOICE, len(voice))
print("---- DRAFT ----")
print(draft)
print("---- VOICE ----")
print(voice)
