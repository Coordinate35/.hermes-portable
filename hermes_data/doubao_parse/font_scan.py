#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描系统字体，找出对归档文本全覆盖的 CJK 字体。"""
import glob, os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SRC = "/home/coordinate35/hermes_data/doubao_threads/2026-09-20_制作日本财政数据与金油比复合总表PPT/会话记录_制作日本财政数据与金油比复合总表PPT.md"
text = open(SRC, encoding="utf-8").read()
CHARS = {ord(c) for c in text if ord(c) > 127}
print("total unique non-ascii:", len(CHARS))

fonts = []
for pat in ("/usr/share/fonts/**/*.tt[cf]", "/usr/share/fonts/**/*.otf", "/usr/local/share/fonts/**/*.tt[cf]", os.path.expanduser("~/.fonts/**/*.tt[cf]"), os.path.expanduser("~/.local/share/fonts/**/*.tt[cf]")):
    fonts.extend(glob.glob(pat, recursive=True))
print("font files found:", len(fonts))

results = []
for i, fp in enumerate(fonts):
    try:
        name = f"F{i}"
        pdfmetrics.registerFont(TTFont(name, fp))
        cmap = getattr(pdfmetrics.getFont(name).face, "charToGlyph", {}) or {}
        missing = sorted(chr(c) for c in CHARS if c not in cmap)
        results.append((len(missing), fp, missing[:30]))
    except Exception as e:
        results.append((99999, fp, [str(e)[:50]]))

results.sort(key=lambda x: x[0])
for n, fp, miss in results[:15]:
    print(n, fp, "miss:", "".join(miss) if miss else "-")
