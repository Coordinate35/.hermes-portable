#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把会话记录 markdown（受控子集：# / > / ## / ### / - / 1. / ``` 围栏 / 段落）渲染为 PDF。
用法: python3 md2pdf_transcript.py <in.md> <out.pdf> <页脚文字>
"""
import os, re, sys, html

SRC, PDF_PATH, FOOTER = sys.argv[1], sys.argv[2], sys.argv[3]

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# font selection with coverage check
text_all = open(SRC, encoding="utf-8").read()
TEST_SET = {ord(c) for c in text_all if ord(c) > 127}
# PDF 渲染层等效替换（md 保留原文）：､ 全字体缺失，视觉等效全角顿号
REPLACE = {"\uff64": "\u3001"}
FONT = None
for _i, _p in enumerate([
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]):
    if not os.path.exists(_p):
        continue
    try:
        _name = f"CJK{_i}"
        pdfmetrics.registerFont(TTFont(_name, _p))
        _cmap = getattr(pdfmetrics.getFont(_name).face, "charToGlyph", {}) or {}
        _missing = [chr(c) for c in TEST_SET if c not in _cmap and chr(c) not in REPLACE]
        if _missing:
            print(f"[font] skip {_p}: missing {' '.join(repr(m) for m in _missing[:20])}")
            continue
        FONT = _name
        print(f"[font] OK {_p}")
        break
    except Exception as e:
        print(f"[font] fail {_p}: {e}")
if not FONT:
    print("PDF_FONT_FAIL"); sys.exit(3)

TITLE = ParagraphStyle("t", fontName=FONT, fontSize=16, leading=23, alignment=1,
                       textColor=colors.HexColor("#1a1a1a"), spaceAfter=8)
META = ParagraphStyle("m", fontName=FONT, fontSize=8.6, leading=13, wordWrap="CJK",
                      textColor=colors.HexColor("#666666"), spaceAfter=2)
H2 = ParagraphStyle("h2", fontName=FONT, fontSize=12.5, leading=18, wordWrap="CJK",
                    textColor=colors.HexColor("#1f3b57"), spaceBefore=12, spaceAfter=5)
H3 = ParagraphStyle("h3", fontName=FONT, fontSize=10.5, leading=16, wordWrap="CJK",
                    textColor=colors.HexColor("#7a1f2b"), spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("b", fontName=FONT, fontSize=9.3, leading=14.5, wordWrap="CJK",
                      textColor=colors.HexColor("#222222"), spaceAfter=4)
BULL = ParagraphStyle("bl", parent=BODY, leftIndent=14, bulletIndent=2)
CODE = ParagraphStyle("c", fontName=FONT, fontSize=7.6, leading=11.2, wordWrap="CJK",
                      textColor=colors.HexColor("#333333"), backColor=colors.HexColor("#f6f6f6"),
                      borderPadding=4, leftIndent=6, rightIndent=0, spaceBefore=2, spaceAfter=6)

def esc(t):
    t = t.replace("**", "")
    for _k, _v in REPLACE.items():
        t = t.replace(_k, _v)
    return html.escape(t)

def esc_join(lines):
    """逐行转义后用 <br/> 连接（先转义再拼标签，避免标签被转义）。"""
    return "<br/>".join(esc(x) for x in lines)

story = []
lines = text_all.split("\n")
in_code = False
code_buf = []
para_buf = []

def flush_para():
    global para_buf
    if para_buf:
        story.append(Paragraph(esc_join(para_buf), BODY))
        para_buf = []

for ln in lines:
    s = ln.rstrip()
    if s.strip().startswith("```"):
        if in_code:
            story.append(Paragraph(esc_join(code_buf), CODE))
            code_buf, in_code = [], False
        else:
            flush_para()
            in_code = True
        continue
    if in_code:
        code_buf.append(s)
        continue
    st = s.strip()
    if not st:
        flush_para()
        continue
    if st == "---":
        flush_para()
        continue
    if st.startswith("# "):
        flush_para(); story.append(Paragraph(esc(st[2:]), TITLE)); continue
    if st.startswith("> "):
        flush_para(); story.append(Paragraph(esc(st[2:]), META)); continue
    if st.startswith("## "):
        flush_para(); story.append(Paragraph(esc(st[3:]), H2)); continue
    if st.startswith("### "):
        flush_para()
        nxt = Paragraph(esc(st[4:]), H3)
        story.append(nxt)
        continue
    if re.match(r"^[-*] ", st):
        flush_para(); story.append(Paragraph("• " + esc(st[2:]), BULL)); continue
    if re.match(r"^\d+\. ", st):
        flush_para(); story.append(Paragraph(esc(st), BULL)); continue
    para_buf.append(st)
flush_para()
if in_code and code_buf:
    story.append(Paragraph(esc_join(code_buf), CODE))

def footer(canv, doc):
    canv.saveState()
    canv.setFont(FONT, 7.5)
    canv.setFillColor(colors.HexColor("#999999"))
    canv.drawCentredString(A4[0] / 2, 1.0 * cm, f"{FOOTER} · 第 {doc.page} 页")
    canv.restoreState()

doc = SimpleDocTemplate(PDF_PATH, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm,
                        topMargin=1.6*cm, bottomMargin=1.8*cm, title="豆包会话归档")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("PDF_OK:", PDF_PATH, os.path.getsize(PDF_PATH), "bytes")
