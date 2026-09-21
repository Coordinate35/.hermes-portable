#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装豆包会话归档：转录 markdown + PDF + 文件复制 + 幻灯片 PDF。"""
import json, os, re, shutil, html as h
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
WS = "/home/coordinate35/.hermes/cache/browser-use/workspace/20260921_111906_10d5ec90"
PARSE = "/home/coordinate35/hermes_data/doubao_parse"
OUTBASE = "/home/coordinate35/hermes_data/doubao_threads"

pay = json.load(open(f"{PARSE}/share_payload.json", encoding="utf-8"))
share = pay["data"]["share_info"]
msgs = pay["data"]["message_snapshot"]["message_list"]

share_dt = datetime.fromtimestamp(int(share["share_time"]) / 1000, tz=CST)
date_s = share_dt.strftime("%Y-%m-%d")
time_s = share_dt.strftime("%Y-%m-%d %H:%M")
arch_dt = datetime.now(CST)

ARCH = f"{OUTBASE}/{date_s}_制作日本财政数据与金油比复合总表PPT"

def fmt_block(b):
    """Render one content block to markdown lines (verbatim content)."""
    bt = b.get("block_type")
    c = b.get("content") or {}
    lines = []
    if bt == 10000 and "text_block" in c:
        lines.append(c["text_block"].get("text", ""))
    elif bt == 10040 and "thinking_block" in c:
        lines.append(f"### ［步骤］{c['thinking_block'].get('finish_title', '')}")
    elif bt == 10019 and "file_operation_block" in c:
        fb = c["file_operation_block"]
        summ = (fb.get("header") or {}).get("summary", "")
        title = f"### ［文件操作］{summ}" if summ else "### ［文件操作］"
        lines.append(title)
        path = fb.get("path") or ""
        fname = fb.get("file_name") or ""
        if path:
            lines.append(f"文件：`{path}`")
        if fname and fname not in path:
            lines.append(f"文件名：`{fname}`")
        content = (fb.get("content") or "").strip()
        if content:
            lines.append("```text")
            lines.append(content)
            lines.append("```")
    elif bt == 10025 and "search_query_result_block" in c:
        sb = c["search_query_result_block"]
        lines.append(f"### ［联网搜索］{sb.get('summary', '')}")
        qs = sb.get("queries") or []
        if qs:
            lines.append("关键词：" + "、".join(f"`{q}`" for q in qs))
        for i, r in enumerate(sb.get("results") or [], 1):
            tc = r.get("text_card") or {}
            t = (tc.get("title") or "").replace("\n", " ")
            u = tc.get("url") or ""
            lines.append(f"{i}. {t} — {u}")
    elif bt == 10030 and "artifact_block" in c:
        ab = c["artifact_block"]
        lines.append(f"### ［产出文件（飞书幻灯片）］{ab.get('title', '')}")
        lines.append(f"- 资源ID：`{ab.get('resource_id')}`（类型 {ab.get('resource_type')}，内容类型 {ab.get('resource_content_type')}）")
        if "XQ7OsiOX5ll2hGdBnO6cHHlxnqd" in str(ab.get("resource_id")):
            lines.append("- 在线地址：https://my.feishu.cn/slides/XQ7OsiOX5ll2hGdBnO6cHHlxnqd")
        bi = ab.get("brief_image") or {}
        pu = ((bi.get("image_preview") or {}).get("url")) or ""
        if pu:
            lines.append(f"- 预览图（豆包内网链接，需登录）：{pu}")
    else:
        lines.append(f"### ［未识别块 type={bt}］")
        lines.append("```json")
        lines.append(json.dumps(c, ensure_ascii=False, indent=1))
        lines.append("```")
    return lines

# ---------- build transcript ----------
md = []
md.append("# 制作日本财政数据与金油比复合总表PPT —— 豆包工作会话归档")
md.append("")
md.append(f"> **分享标题**：{share.get('share_name')}")
md.append(f"> **分享者**：{share['user']['nick_name']}（豆包账号昵称）")
md.append(f"> **分享时间**：{time_s}（CST）")
md.append("> **来源链接**：https://www.doubao.com/thread/xJmJw8EFjJAgSqdTv")
md.append(f"> **分享ID**：{share.get('share_id')}")
md.append(f"> **归档时间**：{arch_dt.strftime('%Y-%m-%d %H:%M')}（CST）")
md.append("> **归档说明**：该分享链接仅含最后一轮对话（用户消息 1 条 + 豆包 Agent 回复 1 条，共 52 个内容块，含思考步骤、联网搜索引用与文件操作记录）。完整会话历史需登录豆包查看。Agent 产出的飞书幻灯片《金油比×日本财政：1971-2025复合总表》共 2 页，截图与 PDF 见 files/ 目录，原始数据见 raw/ 目录。")
md.append("")
md.append("---")
md.append("")

for m in msgs:
    ut = m.get("user_type")
    t = datetime.fromtimestamp(int(m.get("create_time", 0)), tz=CST).strftime("%Y-%m-%d %H:%M:%S")
    who = "用户" if ut == 1 else "豆包 Agent 回复"
    md.append(f"## {who}（{t}）")
    md.append("")
    content = m.get("content") or "[]"
    try:
        blocks = json.loads(content)
    except Exception:
        blocks = []
    if isinstance(blocks, dict):
        blocks = [blocks]
    for b in blocks:
        md.extend(fmt_block(b))
        md.append("")
    md.append("---")
    md.append("")

# appendix
md.append("## 附录：归档文件清单")
md.append("")
md.append("- `会话记录_制作日本财政数据与金油比复合总表PPT.md` / `.pdf`：本文件（逐字记录）")
md.append("- `files/金油比×日本财政_1971-2025复合总表_第1页_复合总表.png`：幻灯片第 1 页高清截图（2488×1472）")
md.append("- `files/金油比×日本财政_1971-2025复合总表_第2页_黄金还原法.png`：幻灯片第 2 页高清截图（2488×1472）")
md.append("- `files/金油比×日本财政_1971-2025复合总表_全2页.pdf`：两页截图合成的 PDF")
md.append("- `files/幻灯片文字版_两页.txt`：从在线幻灯片提取的两页文字内容")
md.append("- `raw/share_payload.json`：分享页完整解码数据（含全部字段）")
md.append("- `raw/share_page.html`：分享页原始 HTML 快照")
md.append("")
md.append("---")
md.append("")
md.append(f"*注：幻灯片在线版可编辑地址 https://my.feishu.cn/slides/XQ7OsiOX5ll2hGdBnO6cHHlxnqd（登录飞书可见）；数据来源与时间范围以幻灯片页脚标注为准。转录时间 {arch_dt.strftime('%Y-%m-%d')}（CST）。*")

md_text = "\n".join(md)

os.makedirs(ARCH, exist_ok=True)
os.makedirs(f"{ARCH}/files", exist_ok=True)
os.makedirs(f"{ARCH}/raw", exist_ok=True)

md_path = f"{ARCH}/会话记录_制作日本财政数据与金油比复合总表PPT.md"
open(md_path, "w", encoding="utf-8").write(md_text)
print("MD saved:", md_path, len(md_text), "chars")

# raw copies
shutil.copy(f"{PARSE}/share_payload.json", f"{ARCH}/raw/share_payload.json")
shutil.copy("/tmp/doubao_thread.html", f"{ARCH}/raw/share_page.html")
print("raw copied")

# slide images
shutil.copy(f"{WS}/slide_01.png", f"{ARCH}/files/金油比×日本财政_1971-2025复合总表_第1页_复合总表.png")
shutil.copy(f"{WS}/slide_02.png", f"{ARCH}/files/金油比×日本财政_1971-2025复合总表_第2页_黄金还原法.png")
print("slide pngs copied")

# slide text combined
t1 = open(f"{WS}/slide_01_text.txt", encoding="utf-8").read()
t2 = open(f"{WS}/slide_02_text.txt", encoding="utf-8").read()
open(f"{ARCH}/files/幻灯片文字版_两页.txt", "w", encoding="utf-8").write(
    "== 第 1 页：复合总表 ==\n\n" + t1 + "\n\n" + "== 第 2 页：方法论·黄金还原法 ==\n\n" + t2)
print("slide text saved")

# slide PDF from PNGs (PIL)
from PIL import Image
im1 = Image.open(f"{ARCH}/files/金油比×日本财政_1971-2025复合总表_第1页_复合总表.png").convert("RGB")
im2 = Image.open(f"{ARCH}/files/金油比×日本财政_1971-2025复合总表_第2页_黄金还原法.png").convert("RGB")
pdf_slide = f"{ARCH}/files/金油比×日本财政_1971-2025复合总表_全2页.pdf"
im1.save(pdf_slide, "PDF", resolution=200.0, save_all=True, append_images=[im2])
print("slide PDF saved:", pdf_slide, os.path.getsize(pdf_slide), "bytes")
print("ARCHIVE DIR:", ARCH)
