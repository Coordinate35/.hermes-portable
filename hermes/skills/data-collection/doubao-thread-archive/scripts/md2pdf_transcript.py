#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""受控 markdown 子集 -> PDF（中文友好，reportlab + wqy-zenhei）。
支持: # / > / ## / ### / - / 1. / ``` 围栏 / 段落。
用法: python3 md2pdf_transcript.py <in.md> <out.pdf> "<页脚文字>"
需用 rl-venv: ~/hermes_data/rl-venv/bin/python
注意:
  - <br/> 必须"先逐行 html.escape 再拼标签"，否则标签会被转义成字面文本。
  - wqy-zenhei 缺 '､'(U+FF64)，渲染层替换为 '、'（md 保留原文）。
"""
import os, re, sys, html

SRC, PDF_PATH, FOOTER = sys.argv[1], sys.argv[2], sys.argv[3]

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

text_all = open(SRC, encoding="utf-8").read()
TEST_SET = {ord(c) for c in text_all if ord(c) > 127}
REPLACE = {"\uff64": "\u3001", "\U0001F449": "\u2192"}  # ､→、；👉→→（wqy 无 emoji 字形）
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
TABLE = ParagraphStyle("tb", fontName=FONT, fontSize=8.4, leading=13, wordWrap="CJK",
                       textColor=colors.HexColor("#2b2b2b"), backColor=colors.HexColor("#faf7f2"),
                       borderPadding=4, leftIndent=6, rightIndent=6, spaceBefore=2, spaceAfter=6)

def latex_cleanup(t):
    """PDF 显示层：常见 LaTeX 转 Unicode（md 保留原文）。"""
    t = re.sub(r"\\boldsymbol\{([^}]*)\}", r"\1", t)
    for _a, _b in [("\\times", "×"), ("\\approx", "≈"), ("\\div", "÷"), ("\\cdot", "·"),
                   ("\\pm", "±"), ("\\leq", "≤"), ("\\geq", "≥"), ("\\rightarrow", "→")]:
        t = t.replace(_a, _b)
    t = re.sub(r"\$([^$\n]*=[^$\n]*)\$", r"\1", t)
    return t

def esc(t):
    t = t.replace("**", "")
    t = latex_cleanup(t)
    for _k, _v in REPLACE.items():
        t = t.replace(_k, _v)
    return html.escape(t)

def esc_join(lines):
    return "<br/>".join(esc(x) for x in lines)

story = []
lines = text_all.split("\n")
in_code = False
code_buf = []
para_buf = []
table_buf = []

def flush_para():
    global para_buf
    if para_buf:
        story.append(Paragraph(esc_join(para_buf), BODY))
        para_buf = []

def flush_table():
    global table_buf
    if table_buf:
        rows = []
        for r in table_buf:
            cells = [c.strip() for c in r.strip("|").split("|")]
            if cells and all(re.fullmatch(r"[-: ]+", c) for c in cells):
                continue  # |---|---| 分隔行
            rows.append(" | ".join(cells))
        story.append(Paragraph(esc_join(rows), TABLE))
        table_buf = []

for ln in lines:
    s = ln.rstrip()
    if s.strip().startswith("```"):
        if in_code:
            story.append(Paragraph(esc_join(code_buf), CODE))
            code_buf, in_code = [], False
        else:
            flush_para(); flush_table()
            in_code = True
        continue
    if in_code:
        code_buf.append(s)
        continue
    st = s.strip()
    if not st or st == "---":
        flush_para(); flush_table()
        continue
    if st.startswith("|"):
        flush_para()
        table_buf.append(st)
        continue
    if table_buf:
        flush_table()
    if st.startswith("# "):
        flush_para(); story.append(Paragraph(esc(st[2:]), TITLE)); continue
    if st.startswith("> "):
        flush_para(); story.append(Paragraph(esc(st[2:]), META)); continue
    if st.startswith("## "):
        flush_para(); story.append(Paragraph(esc(st[3:]), H2)); continue
    if st.startswith("### "):
        flush_para(); story.append(Paragraph(esc(st[4:]), H3)); continue
    if re.match(r"^[-*] ", st):
        flush_para(); story.append(Paragraph("• " + esc(st[2:]), BULL)); continue
    if re.match(r"^\d+\. ", st):
        flush_para(); story.append(Paragraph(esc(st), BULL)); continue
    para_buf.append(st)
flush_para()
flush_table()
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
