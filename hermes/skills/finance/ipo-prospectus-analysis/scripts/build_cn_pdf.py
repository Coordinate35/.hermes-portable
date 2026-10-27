#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文长文档 markdown → PDF（支持 #/##/### 标题、- 列表、| 管道表格）。

用法（必须带 PYTHONPATH= 前缀，避免 Hermes 注入的 3.14 包污染 rl-venv）：
  PYTHONPATH= ~/hermes_data/rl-venv/bin/python build_cn_pdf.py 稿.md
输出：同目录同名 .pdf

约定：
- 首行 `# 标题`；`> 元信息` 行居中灰色小字
- `## 一、xxx` / `### 1.1 xxx` 分节
- `| a | b |` 表格；`| --- | --- |` 分隔行可省略
- 数字列自动识别并右对齐（wordWrap='LTR'，防止长数字折行）
"""
import os
import re
import sys

SRC = sys.argv[1]
PDF = os.path.splitext(SRC)[0] + '.pdf'

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT = None
for i, p in enumerate([
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf']):
    if os.path.exists(p):
        try:
            pdfmetrics.registerFont(TTFont(f'CJK{i}', p))
            FONT = f'CJK{i}'
            break
        except Exception:
            pass
if not FONT:
    print('PDF_FONT_FAIL')
    sys.exit(3)

# 中文避头标点补全（reportlab 原生漏掉全角逗号/叹号/问号等）
try:
    from reportlab.lib import textsplit as _ts
    from reportlab.platypus import paragraph as _pp
    extra = '\uff0c\uff01\uff1f\uff1b\uff1a\uff0e\u201d\u2019'
    _ts.ALL_CANNOT_START += extra
    _pp.ALL_CANNOT_START += extra
except Exception:
    pass

TITLE = ParagraphStyle('t', fontName=FONT, fontSize=19, leading=27, alignment=1,
                       textColor=colors.HexColor('#12263a'), spaceAfter=6)
META = ParagraphStyle('m', fontName=FONT, fontSize=8.2, leading=13, alignment=1,
                      textColor=colors.HexColor('#666666'), spaceAfter=2)
H2 = ParagraphStyle('h2', fontName=FONT, fontSize=14, leading=21,
                    textColor=colors.HexColor('#1f3b57'), spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle('h3', fontName=FONT, fontSize=11.6, leading=18,
                    textColor=colors.HexColor('#2b4f6e'), spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle('b', fontName=FONT, fontSize=10.8, leading=18.2,
                      textColor=colors.HexColor('#222222'), spaceAfter=5.5,
                      wordWrap='CJK', firstLineIndent=21)
BULLET = ParagraphStyle('bl', parent=BODY, firstLineIndent=0, leftIndent=14,
                        bulletIndent=4, spaceAfter=3.5)
CELL = ParagraphStyle('c', fontName=FONT, fontSize=8.2, leading=11.6,
                      textColor=colors.HexColor('#1a1a1a'), wordWrap='CJK')
CELLR = ParagraphStyle('cr', parent=CELL, alignment=2, wordWrap='LTR')
CELLS = ParagraphStyle('cs', parent=CELL, fontSize=7.6, leading=10.4)
CELLSR = ParagraphStyle('csr', parent=CELLS, fontSize=7.2, alignment=2, wordWrap='LTR')
CELLH = ParagraphStyle('ch', parent=CELL, textColor=colors.white)


def esc(s):
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)


def parse(path):
    blocks, meta, title = [], [], ''
    cur = []

    def flush():
        nonlocal cur
        if cur:
            blocks.append(('table', cur))
            cur = []

    for raw in open(path, encoding='utf-8'):
        s = raw.rstrip('\n').strip()
        if not s:
            continue
        if s.startswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                continue
            cur.append(cells)
            continue
        flush()
        if s.startswith('# ') and not title:
            title = s[2:].strip()
        elif s.startswith('> '):
            meta.append(s[2:].strip())
        elif s.startswith('### '):
            blocks.append(('h3', s[4:].strip()))
        elif s.startswith('## '):
            blocks.append(('h2', s[3:].strip()))
        elif s.startswith('- '):
            blocks.append(('bullet', s[2:].strip()))
        elif s == '---':
            continue
        else:
            blocks.append(('p', s))
    flush()
    return title, meta, blocks


def widths(rows, numcol, avail):
    ncol = max(len(r) for r in rows)
    w = []
    for i in range(ncol):
        if i == 0:
            w.append(2.4 if ncol >= 6 else 3.2)
        elif numcol[i]:
            w.append(1.0)
        else:
            w.append(1.6)
    tot = sum(w)
    return [avail * x / tot for x in w]


title, meta, blocks = parse(SRC)
doc = SimpleDocTemplate(PDF, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                        title=title, author='Hermes 中文精译')
avail = doc.width
story = [Paragraph(esc(title), TITLE), Spacer(1, 2)]
for m in meta:
    story.append(Paragraph(esc(m), META))
story.append(Spacer(1, 8))

for kind, val in blocks:
    if kind == 'h2':
        story.append(Paragraph(esc(val), H2))
    elif kind == 'h3':
        story.append(Paragraph(esc(val), H3))
    elif kind == 'bullet':
        story.append(Paragraph(esc(val), BULLET, bulletText='•'))
    elif kind == 'p':
        story.append(Paragraph(esc(val), BODY))
    else:
        rows = val
        ncol = max(len(r) for r in rows)
        norm = [(r + [''] * (ncol - len(r))) for r in rows]

        def isnum(c):
            c2 = c.replace(',', '').replace('$', '').strip()
            return bool(re.search(r'\d', c2)) and bool(re.fullmatch(r'[\d\.\-\(\)%\sA-Za-z]+', c2))

        numcol = []
        for ci in range(ncol):
            vals = [r[ci] for r in norm[1:] if r[ci].strip()]
            numcol.append(ci > 0 and bool(vals) and all(isnum(v) for v in vals))

        data = []
        for ri, r in enumerate(norm):
            row = []
            for ci, c in enumerate(r):
                if ri == 0:
                    st = CELLH
                elif numcol[ci]:
                    st = CELLSR if ncol >= 6 else CELLR
                else:
                    st = CELLS if ncol >= 6 else CELL
                row.append(Paragraph(esc(c), st))
            data.append(row)
        t = Table(data, colWidths=widths(norm, numcol, avail), repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b4f6e')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#b9c6d2')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f7fa')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(Spacer(1, 3))
        story.append(t)
        story.append(Spacer(1, 6))


def footer(canv, docu):
    canv.saveState()
    canv.setFont(FONT, 7.5)
    canv.setFillColor(colors.HexColor('#888888'))
    canv.drawCentredString(A4[0] / 2, 1.0 * cm, f'第 {docu.page} 页')
    canv.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('OK', PDF, os.path.getsize(PDF))
