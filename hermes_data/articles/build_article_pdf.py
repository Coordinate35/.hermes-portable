#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把文章 markdown（article-archive 格式：标题/元信息/正文/图注/尾注）转为 PDF。
用法: python3 build_article_pdf.py [文章.md]
默认转换: ~/hermes_data/articles/潘功胜_深刻认识中国金融结构变迁_求是2026年第18期_20260916.md
输出: 同目录同名 .pdf ｜ 依赖: reportlab + wqy 字体（~/hermes_data/rl-venv）
"""
import os
import re
import sys
import html

DEFAULT_SRC = "/home/coordinate35/hermes_data/articles/潘功胜_深刻认识中国金融结构变迁_求是2026年第18期_20260916.md"
SRC = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
if not os.path.exists(SRC):
    print("SRC_NOT_FOUND:", SRC)
    sys.exit(1)
PDF_PATH = os.path.splitext(SRC)[0] + ".pdf"

# ---------------- 解析 markdown ----------------
meta = []
blocks = []  # (kind, text): title/head/sub/p/cap/note
with open(SRC, encoding="utf-8") as f:
    lines = f.read().split("\n")

for ln in lines:
    s = ln.strip()
    if not s:
        continue
    if s.startswith("# ") and not blocks and not meta:
        blocks.append(("title", s[2:].strip()))
    elif s.startswith(">"):
        meta.append(s[1:].strip().replace("**", ""))
    elif s == "---":
        continue
    elif s.startswith("**") and s.endswith("**") and len(s) > 4:
        blocks.append(("head", s.strip("*").strip()))
    elif s.startswith("!["):
        _m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", s)
        blocks.append(("img", _m.group(1)) if _m else ("p", s))
    elif s.startswith("［图注］"):
        blocks.append(("cap", s))
    elif s.startswith("*——") and s.endswith("*"):
        blocks.append(("note", s.strip("*").strip()))
    elif re.match(r"^第[一二三四五六]，", s):
        blocks.append(("sub", s))
    else:
        blocks.append(("p", s))

print("blocks:", len(blocks), " meta lines:", len(meta))

# ---------------- reportlab ----------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether, Image
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image as PILImage
except Exception as e:  # noqa
    print("REPORTLAB_MISSING:", e)
    sys.exit(2)

all_texts = meta + [t for k, t in blocks if k != "img"]
TEST_SET = {ord(c) for t in all_texts for c in t if ord(c) > 127}
print("non-ASCII charset size:", len(TEST_SET))

FONT = None
CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]
for _i, _p in enumerate(CANDIDATES):
    if not os.path.exists(_p):
        continue
    try:
        _name = f"CJK{_i}"
        pdfmetrics.registerFont(TTFont(_name, _p))
        _cmap = getattr(pdfmetrics.getFont(_name).face, "charToGlyph", {}) or {}
        _missing = sorted(chr(c) for c in TEST_SET if c not in _cmap)
        if _missing:
            print(f"[font] skip {_p}: missing {''.join(_missing)[:50]}")
            continue
        FONT = _name
        print(f"[font] OK {_p} (full charset covered)")
        break
    except Exception as e:
        print(f"[font] fail {_p}: {e}")
if not FONT:
    print("PDF_FONT_FAIL")
    sys.exit(3)

# ---------------- 样式与文档 ----------------
TITLE = ParagraphStyle("t", fontName=FONT, fontSize=17, leading=24, alignment=1,
                       textColor=colors.HexColor("#1a1a1a"), spaceAfter=8)
META = ParagraphStyle("m", fontName=FONT, fontSize=8.5, leading=13.5,
                      textColor=colors.HexColor("#666666"), spaceAfter=1.5)
HEAD = ParagraphStyle("h", fontName=FONT, fontSize=12.5, leading=19,
                      textColor=colors.HexColor("#1f3b57"), spaceBefore=10, spaceAfter=5)
BODY = ParagraphStyle("b", fontName=FONT, fontSize=10, leading=16,
                      textColor=colors.HexColor("#222222"), firstLineIndent=20, spaceAfter=4.5)
SUB = ParagraphStyle("s", parent=BODY, firstLineIndent=0, spaceBefore=3, spaceAfter=3)
CAP = ParagraphStyle("c", fontName=FONT, fontSize=8.8, leading=13.5,
                     textColor=colors.HexColor("#777777"), alignment=1, spaceAfter=8)
NOTE = ParagraphStyle("n", fontName=FONT, fontSize=8.5, leading=13,
                      textColor=colors.HexColor("#888888"), alignment=1, spaceBefore=5)

story = []
for kind, text in blocks:
    if kind == "title":
        story.append(Paragraph(html.escape(text), TITLE))
    elif kind == "head":
        story.append(Paragraph(html.escape(text), HEAD))
    elif kind == "sub":
        story.append(Paragraph(html.escape(text), SUB))
    elif kind == "img":
        _ipath = text if os.path.isabs(text) else os.path.join(os.path.dirname(os.path.abspath(SRC)), text)
        if os.path.exists(_ipath):
            _iw, _ih = PILImage.open(_ipath).size
            _w = 12.0 * cm
            _h = _w * _ih / _iw
            if _h > 12.0 * cm:
                _h = 12.0 * cm
                _w = _h * _iw / _ih
            story.append(Spacer(1, 6))
            story.append(Image(_ipath, width=_w, height=_h, hAlign="CENTER"))
        else:
            print("[img] MISSING:", _ipath)
    elif kind == "cap":
        story.append(Paragraph(html.escape(text), CAP))
    elif kind == "note":
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#cccccc"), spaceBefore=10, spaceAfter=6))
        story.append(Paragraph(html.escape(text), NOTE))
    else:
        story.append(Paragraph(html.escape(text), BODY))
# 章节标题与后段保持同页（防“标题孤行”）
_wrapped = []
_j = 0
while _j < len(story):
    _el = story[_j]
    _is_head = (isinstance(_el, Paragraph)
                and getattr(getattr(_el, "style", None), "name", "") == "h")
    _is_img = isinstance(_el, Image)
    if (_is_head or _is_img) and _j + 1 < len(story) and isinstance(story[_j + 1], Paragraph):
        _wrapped.append(KeepTogether([_el, story[_j + 1]]))
        _j += 2
        continue
    _wrapped.append(_el)
    _j += 1
story = _wrapped

# 元信息块+分隔线 插到标题之后
new_story = [story[0]]
new_story.append(Spacer(1, 2))
for m in meta:
    new_story.append(Paragraph(html.escape(m), META))
new_story.append(HRFlowable(width="100%", thickness=0.7,
                            color=colors.HexColor("#999999"), spaceBefore=4, spaceAfter=8))
new_story.extend(story[1:])
story = new_story


def footer(canv, doc):
    canv.saveState()
    canv.setFont(FONT, 7.5)
    canv.setFillColor(colors.HexColor("#999999"))
    canv.drawCentredString(A4[0] / 2, 1.0 * cm,
                           f"潘功胜 · 《求是》2026年第18期 · 第 {doc.page} 页")
    canv.restoreState()


doc = SimpleDocTemplate(PDF_PATH, pagesize=A4,
                        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title="深刻认识中国金融结构变迁 提升金融服务实体经济适配性",
                        author="潘功胜")
try:
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
except Exception as e:
    print("PDF_FAIL:", e)
    sys.exit(4)
print("PDF_OK:", PDF_PATH)
print("PARA/HEAD/CAP counts:", len(blocks))
