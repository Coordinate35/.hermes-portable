#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build voice text for 2026-10-08 10:30 batch, sourced from authoritative raw_texts.
口播改写规则与 10:26 轮（同链条上一条交付）保持一致。"""
import json
import os
import re

BASE = os.path.expanduser("~/hermes_data/weibo_data")
ids = ["5351689555283007", "5351693232899262", "5351693445235128"]


def clean(t: str) -> str:
    # 汉字直连 //@（链段无标点衔接）→ 补句号，如「这么大//@卢麒元」
    t = re.sub(r"(?<=[\u4e00-\u9fff])//@", "。//@", t)
    # 链前缀：//@X: → 转发X： ；回复@X: → 回复X：
    t = re.sub(r"//@([^:：]{1,30}):", r"转发\1：", t)
    t = re.sub(r"回复@([^:：]{1,30}):", r"回复\1：", t)
    # 表情符口语化（数量+种类）
    t = t.replace("。[祈祷]", "，一个祈祷。")
    t = t.replace("。[努力]", "，一个努力。")
    t = t.replace("：[握手]", "：一个握手。")
    # 半角括号串音（沿用 10:26 轮读法）
    t = t.replace(" (HKIC)，", "，HKIC，")
    # 百分比中文读法
    t = t.replace("60%", "百分之六十").replace("30%", "百分之三十").replace("10%", "百分之十")
    # 用户名数字读法
    t = t.replace("MCH2017", "MCH二零一七")
    # 我子睿 留言空格 → 逗号
    t = t.replace("卢老师 如果你长期容易感冒反复  可以试试 吃几天玉屏风颗粒。",
                  "卢老师，如果你长期容易感冒反复，可以试试，吃几天玉屏风颗粒。")
    t = t.rstrip()
    # 截断止点照读、补句号
    if not t.endswith("。"):
        t += "。"
    return t


texts = []
for wid in ids:
    with open(f"{BASE}/wb_verify_{wid}.json", encoding="utf-8") as f:
        rt = json.load(f)["raw_text"]
    texts.append(clean(rt))

voice = ("卢麒元发布新微博，三条。第一条，" + texts[0]
         + "第二条，" + texts[1]
         + "第三条，" + texts[2])

with open("/tmp/voice_text_wb_20261008_1030.txt", "w", encoding="utf-8") as f:
    f.write(voice)

print("=== V1 ===")
print(texts[0])
print("=== V2 ===")
print(texts[1])
print("=== V3 ===")
print(texts[2])
print(f"=== FULL len={len(voice)} ===")
print(voice)
