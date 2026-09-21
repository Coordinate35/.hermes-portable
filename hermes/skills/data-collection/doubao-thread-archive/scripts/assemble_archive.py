#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 share_payload.json 组装豆包会话归档：逐字转录 md + files/ + raw/ + 幻灯片 PDF。
用法: python3 assemble_archive.py <share_payload.json> <归档目录> [幻灯片图片目录]
  - 幻灯片图片目录内应为 slide_01.png, slide_02.png, ... 及 slide_01_text.txt, ...
    （由浏览器截图流程产出；无则跳过幻灯片部分）
依赖: rl-venv（PIL 合成 PDF）。转录 PDF 另跑 md2pdf_transcript.py。
"""
import json, os, re, shutil, sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)
payload_path, ARCH = sys.argv[1], sys.argv[2]
slides_dir = sys.argv[3] if len(sys.argv) > 3 else None
html_path = sys.argv[4] if len(sys.argv) > 4 else None

pay = json.load(open(payload_path, encoding="utf-8"))
share = pay["data"]["share_info"]
msgs = pay["data"]["message_snapshot"]["message_list"]
share_dt = datetime.fromtimestamp(int(share["share_time"]) / 1000, tz=CST)
time_s = share_dt.strftime("%Y-%m-%d %H:%M")
date_s = share_dt.strftime("%Y-%m-%d")
arch_dt = datetime.now(CST)

def fmt_block(b):
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
        lines.append(f"### ［文件操作］{summ}" if summ else "### ［文件操作］")
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
        # 飞书链接通常在 fileop 的创建命令输出中，另行人工核对；此处如资源ID形似飞书token则提示
        bi = ab.get("brief_image") or {}
        pu = ((bi.get("image_preview") or {}).get("url")) or ""
        if pu:
            lines.append(f"- 预览图（豆包内网链接，需登录）：{pu}")
    elif bt == 10053 and "tips_block" in c:
        lines.append(f"### ［提示］{(c['tips_block'].get('text') or '').strip()}")
    else:
        lines.append(f"### ［未识别块 type={bt}］")
        lines.append("```json")
        lines.append(json.dumps(c, ensure_ascii=False, indent=1))
        lines.append("```")
    return lines

os.makedirs(f"{ARCH}/files", exist_ok=True)
os.makedirs(f"{ARCH}/raw", exist_ok=True)

# raw
shutil.copy(payload_path, f"{ARCH}/raw/share_payload.json")
if html_path and os.path.exists(html_path):
    shutil.copy(html_path, f"{ARCH}/raw/share_page.html")

# slides
slide_files = []
if slides_dir and os.path.isdir(slides_dir):
    names = sorted(f for f in os.listdir(slides_dir) if re.match(r"slide_\d+\.png$", f))
    for i, f in enumerate(names, 1):
        dst = f"{ARCH}/files/幻灯片_第{i}页.png"
        shutil.copy(os.path.join(slides_dir, f), dst)
        slide_files.append(dst)
    if slide_files:
        from PIL import Image
        imgs = [Image.open(p).convert("RGB") for p in slide_files]
        pdf_slide = f"{ARCH}/files/幻灯片_全{len(imgs)}页.pdf"
        imgs[0].save(pdf_slide, "PDF", resolution=200.0, save_all=True, append_images=imgs[1:])
        print("slide PDF:", pdf_slide)
    texts = sorted(f for f in os.listdir(slides_dir) if re.match(r"slide_\d+_text\.txt$", f))
    if texts:
        buf = []
        for i, f in enumerate(texts, 1):
            buf.append(f"== 第 {i} 页 ==\n\n" + open(os.path.join(slides_dir, f), encoding="utf-8").read())
        open(f"{ARCH}/files/幻灯片文字版.txt", "w", encoding="utf-8").write("\n\n".join(buf))

# transcript md
md = []
md.append(f"# {share.get('share_name')} —— 豆包工作会话归档")
md.append("")
md.append(f"> **分享标题**：{share.get('share_name')}")
md.append(f"> **分享者**：{share['user']['nick_name']}（豆包账号昵称）")
md.append(f"> **分享时间**：{time_s}（CST）")
md.append(f"> **来源链接**：{pay.get('canonicalUrl', '')}")
md.append(f"> **分享ID**：{share.get('share_id')}")
md.append(f"> **归档时间**：{arch_dt.strftime('%Y-%m-%d %H:%M')}（CST）")
md.append(f"> **归档说明**：该分享链接仅含最后一轮对话（消息 {len(msgs)} 条）。完整会话历史需登录豆包查看。产出文件截图与 PDF 见 files/ 目录，原始数据见 raw/ 目录。")
md.append("")
md.append("---")
md.append("")
for m in msgs:
    ut = m.get("user_type")
    t = datetime.fromtimestamp(int(m.get("create_time", 0)), tz=CST).strftime("%Y-%m-%d %H:%M:%S")
    who = "用户" if ut == 1 else "豆包 Agent 回复"
    md.append(f"## {who}（{t}）")
    md.append("")
    try:
        blocks = json.loads(m.get("content") or "[]")
    except Exception:
        blocks = []
    if isinstance(blocks, dict):
        blocks = [blocks]
    for b in blocks:
        md.extend(fmt_block(b))
        md.append("")
    md.append("---")
    md.append("")

share_name = (share.get("share_name") or "豆包会话").replace("/", "_")
md.append("## 附录：归档文件清单")
md.append("")
md.append(f"- `会话记录_{share_name}.md` / `.pdf`：本文件（逐字记录）")
for f in sorted(os.listdir(f"{ARCH}/files")):
    md.append(f"- `files/{f}`")
for f in sorted(os.listdir(f"{ARCH}/raw")):
    md.append(f"- `raw/{f}`")
md.append("")
md.append(f"*转录时间 {arch_dt.strftime('%Y-%m-%d')}（CST）。*")

share_name = (share.get("share_name") or "豆包会话").replace("/", "_")
md_path = f"{ARCH}/会话记录_{share_name}.md"
open(md_path, "w", encoding="utf-8").write("\n".join(md))
print("MD saved:", md_path)
print("ARCH:", ARCH)
