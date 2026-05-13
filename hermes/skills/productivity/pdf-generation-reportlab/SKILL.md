---
name: pdf-generation-reportlab
description: Generate professional PDF reports using ReportLab with Chinese font support
author: AI Assistant
date: 2026-01-21
version: 1.0
---

# PDF Report Generation with ReportLab

Generate professional PDF reports using ReportLab with Chinese language support and proper font handling.

## When to Use

- Creating analytical reports with tables and structured content
- Generating Chinese-language documents
- Producing publication-ready PDFs with consistent formatting
- Reports requiring styled tables, multiple heading levels, and page breaks

## Prerequisites

```bash
uv pip install reportlab
```

## Key Lessons from Implementation

### 1. Execute Code is Stateless

**Critical**: Each `execute_code` call runs in a fresh Python process. Variables defined in one call do NOT persist to the next.

```python
# WRONG - This will fail with NameError
# First call:
story = []
story.append(Paragraph("Title", style))

# Second call:
story.append(Paragraph("Content", style))  # NameError: 'story' is not defined

# CORRECT - Define everything in one call
from reportlab.platypus import SimpleDocTemplate, Paragraph
# ... all imports
# ... all variable definitions
# ... all content building
# ... doc.build(story) - everything in ONE execute_code call
```

### 2. Font Registration Strategy

Different Linux distributions store Chinese fonts in different locations. Try multiple paths:

```python
font_paths = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

font_registered = False
font_name = 'Helvetica'  # Fallback

for font_path in font_paths:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Chinese', font_path))
            font_registered = True
            font_name = 'Chinese'
            break
        except:
            continue
```

### 3. Use uv for Package Installation

The environment uses `uv` for package management, not `pip`:

```bash
# Correct
uv pip install reportlab

# Avoid
pip install reportlab  # May not work in this environment
```

### 4. Output Directory Convention

Always save to the user's data directory:

```python
# Correct
output_path = "/home/coordinate35/hermes_data/my_report.pdf"

# Avoid  
output_path = "/home/coordinate35/my_report.pdf"  # Wrong location
```

## Complete Working Template

```python
#!/usr/bin/env python3
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def generate_report(output_path, content_callback):
    # Register Chinese font
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    
    font_registered = False
    font_name = 'Helvetica'
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                font_registered = True
                font_name = 'Chinese'
                break
            except:
                continue
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'],
        fontSize=24, textColor=HexColor('#1a1a1a'),
        spaceAfter=30, alignment=1,
        fontName=font_name
    )
    
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=18, textColor=HexColor('#2c3e50'),
        spaceAfter=12, spaceBefore=12,
        fontName=font_name
    )
    
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=14, textColor=HexColor('#34495e'),
        spaceAfter=10, spaceBefore=10,
        fontName=font_name
    )
    
    normal_style = ParagraphStyle(
        'Normal', parent=styles['Normal'],
        fontSize=11, leading=16,
        fontName=font_name
    )
    
    # Build content
    story = []
    content_callback(story, {
        'title': title_style,
        'h1': h1_style,
        'h2': h2_style,
        'normal': normal_style
    })
    
    doc.build(story)
    return output_path

# Example usage
def add_content(story, styles):
    story.append(Paragraph("报告标题", styles['title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("第一章 核心分析", styles['h1']))
    story.append(Paragraph("这是正文内容...", styles['normal']))

# generate_report("/path/to/output.pdf", add_content)
```

## Table Styling Pattern

```python
# Sample data - list of lists, first row is header
data = [
    ['Column 1', 'Column 2', 'Column 3', 'Column 4'],
    ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3', 'Row 1 Col 4'],
    ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3', 'Row 2 Col 4'],
]

# Create table with column widths
table = Table(data, colWidths=[3*cm, 3*cm, 3*cm, 4*cm])

# Apply styling
table.setStyle(TableStyle([
    # Header row styling
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    
    # Body styling
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    
    # Grid
    ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
    
    # Alternating row colors
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8f9fa')]),
]))

# Add to story
story.append(table)
story.append(Spacer(1, 20))
```

## Common Issues and Solutions

### Issue: `NameError: name 'X' is not defined`

**Cause**: Variables from a previous `execute_code` call don't persist.

**Solution**: Build the entire document in a single `execute_code` call, or write a script file and execute it with the terminal tool.

### Issue: Chinese characters appear as boxes or cause errors

**Cause**: No Chinese font registered or font file not found.

**Solution**: Try multiple font paths and fall back to Helvetica if none work:

```python
font_paths = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
```

### Issue: `ModuleNotFoundError: No module named 'reportlab'`

**Solution**: Use `uv pip install reportlab` instead of `pip install`.

## See Also

- ReportLab documentation: https://www.reportlab.com/docs/
- ReportLab user guide: https://www.reportlab.com/docs/reportlab-userguide.pdf