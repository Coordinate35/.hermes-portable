#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长文内容 -> PDF（微博长文推送的附件交付用）。

用法:
    article_to_pdf.py <input(text|html)> <title> <out.pdf> [meta_line] [link_url]

- input 为 .html 时按微博头条文章 data.content 处理（去标签、</p> 分段、跳过 figure/card）；
  为纯文本时按空行分段。
- 需 reportlab 环境：
    uv venv /tmp/pdfvenv && uv pip install --python /tmp/pdfvenv/bin/python reportlab
  以该 venv 的 python 运行本脚本。
- 字体 wqy-zenhei true-TypeType（reportlab 不支持 Noto CJK CFF 轮廓；TTFError 即此因）。
- 生成后建议 `pdftotext out.pdf -` 抽文本层核验首尾字串。
输出: 一行摘要（size/页数不可得则仅 size）。
"""
import os
import re
import sys
from html import unescape

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from xml.sax.saxutils import escape
except ImportError:
    sys.stderr.write("article_to_pdf: need reportlab -> uv venv /tmp/pdfvenv && "
                     "uv pip install --python /tmp/pdfvenv/bin/python reportlab\n")
    sys.exit(3)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def html_to_text(h: str) -> str:
    h = re.sub(r"<figure[\s\S]*?</figure>", "\n\n", h, flags=re.I)
    h = re.sub(r"<card[^>]*>\s*</card>", "\n\n", h, flags=re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</p>", "\n\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = unescape(h)
    return h


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__.strip())
        return 2
    src, title, out = sys.argv[1], sys.argv[2], sys.argv[3]
    meta = sys.argv[4] if len(sys.argv) > 4 else ""
    link = sys.argv[5] if len(sys.argv) > 5 else ""

    raw = open(src, encoding="utf-8").read()
    if src.lower().endswith((".html", ".htm")):
        raw = html_to_text(raw)
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if not paras:
        print("article_to_pdf: empty content", file=sys.stderr)
        return 4

    name = None
    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("CJK", fp, subfontIndex=0))
                name = fp
                break
            except Exception:
                continue
    if not name:
        print("article_to_pdf: no usable CJK TrueType font", file=sys.stderr)
        return 4

    st_title = ParagraphStyle("t", fontName="CJK", fontSize=17, leading=24, spaceAfter=6)
    st_meta = ParagraphStyle("m", fontName="CJK", fontSize=9, leading=14, textColor=HexColor("#666666"), spaceAfter=16)
    st_h = ParagraphStyle("h", fontName="CJK", fontSize=13, leading=20, spaceBefore=14, spaceAfter=8)
    st_p = ParagraphStyle("p", fontName="CJK", fontSize=11, leading=19, spaceAfter=6)

    def footer(canv, doc):
        canv.saveState()
        canv.setFont("CJK", 9)
        canv.setFillColor(HexColor("#888888"))
        canv.drawCentredString(A4[0] / 2, 1.2 * cm, str(canv.getPageNumber()))
        canv.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2.0 * cm, bottomMargin=2.0 * cm, title=title)
    story = [Paragraph(escape(title), st_title)]
    m = meta + (("<br/>原文链接：" + link) if link else "")
    if m.strip():
        story.append(Paragraph(escape(m).replace("&lt;br/&gt;", "<br/>"), st_meta))
    for i, p in enumerate(paras):
        if i == 0 or re.match(r"^[一二三四五六七八九十]、", p):
            story.append(Paragraph(escape(p), st_h))
        else:
            story.append(Paragraph(escape(p), st_p))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("article_to_pdf: OK", os.path.getsize(out), "bytes ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
