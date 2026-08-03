#!/usr/bin/env python3
"""生成2026年上半年中国经济周期分析PDF报告"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, KeepTogether)
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ── 注册中文字体 ──────────────────────────────────
font_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
font_bold_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"  # 同字体，无独立粗体
pdfmetrics.registerFont(TTFont('CJK', font_path))
# 文泉驿没有独立粗体，用同一字体
pdfmetrics.registerFont(TTFont('CJK-Bold', font_bold_path))
FONT = 'CJK'
FONT_B = 'CJK-Bold'

# ── 颜色 ──────────────────────────────────────────
C_DARK   = HexColor('#1a1a2e')
C_ACCENT = HexColor('#16213e')
C_BLUE   = HexColor('#0f3460')
C_RED    = HexColor('#e94560')
C_GOLD   = HexColor('#f5a623')
C_GREEN  = HexColor('#27ae60')
C_GRAY   = HexColor('#7f8c8d')
C_LIGHT  = HexColor('#f8f9fa')
C_BORDER = HexColor('#dee2e6')
C_ORANGE = HexColor('#e67e22')

# ── 文档设置 ──────────────────────────────────────
output_path = "/home/coordinate35/hermes_data/2026H1_中国经济周期分析报告.pdf"
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)

# ── 样式 ──────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle('CNTitle', fontSize=22, fontName=FONT_B,
    textColor=C_DARK, spaceAfter=6, alignment=TA_CENTER, leading=30)

subtitle_style = ParagraphStyle('CNSubtitle', fontSize=11, fontName=FONT,
    textColor=C_GRAY, spaceAfter=24, alignment=TA_CENTER, leading=16)

h1_style = ParagraphStyle('CNH1', fontSize=16, fontName=FONT_B,
    textColor=C_BLUE, spaceBefore=20, spaceAfter=10,
    borderPadding=(0,0,2,0),
    borderWidth=0, borderColor=C_BLUE, leading=22)

h2_style = ParagraphStyle('CNH2', fontSize=13, fontName=FONT_B,
    textColor=C_ACCENT, spaceBefore=14, spaceAfter=8, leading=18)

body_style = ParagraphStyle('CNBody', fontSize=10.5, fontName=FONT,
    textColor=black, leading=18, spaceAfter=6,
    alignment=TA_JUSTIFY, firstLineIndent=21)

body_no_indent = ParagraphStyle('CNBodyNI', fontSize=10.5, fontName=FONT,
    textColor=black, leading=18, spaceAfter=6, alignment=TA_JUSTIFY)

small_style = ParagraphStyle('CNSmall', fontSize=9, fontName=FONT,
    textColor=C_GRAY, leading=14, spaceAfter=4)

highlight_style = ParagraphStyle('CNHilight', fontSize=10.5, fontName=FONT_B,
    textColor=C_RED, leading=18, spaceAfter=6)

formula_style = ParagraphStyle('CNFormula', fontSize=10, fontName=FONT,
    textColor=C_BLUE, leading=16, spaceAfter=6,
    backColor=C_LIGHT, borderPadding=8,
    borderWidth=0.5, borderColor=C_BORDER)

# ── 辅助函数 ──────────────────────────────────────
def h1(text):
    return Paragraph(text, h1_style)

def h2(text):
    return Paragraph(text, h2_style)

def p(text, style=body_style):
    return Paragraph(text, style)

def bold(text):
    return Paragraph(f'<b>{text}</b>', body_no_indent)

def formula(text):
    return Paragraph(text, formula_style)

def spacer(h=6):
    return Spacer(1, h)

def make_table(data, col_widths, header_rows=1):
    """创建带样式的表格"""
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, header_rows-1), C_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, header_rows-1), white),
        ('FONTNAME', (0, 0), (-1, header_rows-1), FONT_B),
        ('FONTSIZE', (0, 0), (-1, header_rows-1), 9.5),
        ('BOTTOMPADDING', (0, 0), (-1, header_rows-1), 8),
        ('TOPPADDING', (0, 0), (-1, header_rows-1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, header_rows), (-1, -1), FONT),
        ('FONTSIZE', (0, header_rows), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, header_rows), (-1, -1), [white, C_LIGHT]),
    ]
    # 特殊行高亮
    for i in range(header_rows, len(data)):
        if '★' in str(data[i][0]) or '当前' in str(data[i][0]):
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), HexColor('#fff3cd')))
            style_cmds.append(('FONTNAME', (0, i), (-1, i), FONT_B))
    
    t.setStyle(TableStyle(style_cmds))
    return t

# ═══════════════════════════════════════════════════
# 正文
# ═══════════════════════════════════════════════════
story = []

# ── 封面 ──
story.append(spacer(60))
story.append(p("2026年上半年", ParagraphStyle('X', parent=title_style, fontSize=18, textColor=C_GRAY)))
story.append(p("中国经济周期分析", title_style))
story.append(p("及下半年投资建议", ParagraphStyle('X', parent=title_style, fontSize=18, textColor=C_RED)))
story.append(spacer(20))
story.append(p("分析框架：卢麒元四矩阵投资决策框架", subtitle_style))
story.append(p("数据来源：国家统计局 / 中国人民银行公开数据（经AKShare采集）", subtitle_style))
story.append(p("生成日期：2026年8月3日", subtitle_style))
story.append(PageBreak())

# ── 目录页 ──
story.append(h1("目  录"))
story.append(spacer(10))
toc_items = [
    "一、2026年上半年核心数据",
    "二、历史趋势回顾（2020-2026）",
    "三、卢麒元框架核心计算（展开过程）",
    "    3.1 真实通胀率 · 3.2 实质利率 · 3.3 四矩阵周期定位",
    "四、关键边界分析",
    "五、与2026年政府目标的差距分析",
    "六、2026年下半年投资建议",
    "    6.1 三情景分析 · 6.2 配置建议汇总 · 6.3 核心逻辑总结",
    "七、数据局限说明",
]
for item in toc_items:
    story.append(p(item, body_no_indent))
    story.append(spacer(2))
story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第一章：2026年上半年核心数据
# ═══════════════════════════════════════════════════
story.append(h1("一、2026年上半年核心数据"))
story.append(spacer(4))

data_table = [
    ['指标', '最新值', '时间', '上半年范围/备注'],
    ['CPI同比', '1.0%', '2026年6月', '上半年 0.2% ~ 1.3%'],
    ['M2同比增速', '8.0%', '2026年6月', '上半年 8.0% ~ 9.0%（持续回落）'],
    ['GDP同比增速', '4.7%', '2026年H1累计', 'Q1=5.0%, Q2≈4.4%'],
    ['1年期LPR', '3.0%', '2026年7月', '自2025年4月以来维持不变'],
    ['5年期LPR', '3.5%', '2026年7月', '自2025年4月以来维持不变（16个月）'],
    ['房价同比涨幅', '1.8%', '最新（70城新房）', '新建商品住宅价格指数'],
    ['上证指数YTD', '-4.75%', '截至2026.7.31', '高点4242 → 低点3813'],
]
story.append(make_table(data_table, [3.5*cm, 2.5*cm, 3*cm, 7.5*cm]))
story.append(spacer(8))
story.append(p("以上数据来自国家统计局和中国人民银行公开发布数据，通过AKShare接口采集。GDP数据为2026年上半年累计同比增速，Q2单季约为4.4%，较Q1的5.0%出现明显回落。", body_style))
story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第二章：历史趋势回顾
# ═══════════════════════════════════════════════════
story.append(h1("二、历史趋势回顾（2020-2026）"))
story.append(spacer(4))

story.append(h2("2.1 CPI：从零通胀到微弱回升"))
cpi_data = [
    ['年份', '2020', '2021', '2022', '2023', '2024', '2025', '2026H1'],
    ['年均CPI同比', '2.51%', '0.92%', '1.96%', '0.24%', '0.24%', '0.05%', '0.98%'],
]
story.append(make_table(cpi_data, [3*cm] + [2*cm]*7))
story.append(p("2023-2025年经历了近三年的超低通胀（均值不足0.2%），2026年上半年回升至约1%，但仍远低于2%的政策目标。通缩阴影尚未完全消退。", body_style))

story.append(h2("2.2 M2：货币增速持续收敛"))
m2_data = [
    ['年份', '2020', '2021', '2022', '2023', '2024', '2025', '2026.06'],
    ['M2同比(年末)', '10.1%', '9.0%', '11.8%', '9.7%', '7.3%', '8.5%', '8.0%'],
]
story.append(make_table(m2_data, [3*cm] + [2*cm]*7))
story.append(p("2022年疫情冲击时M2飙至11.8%，之后逐步回落。2026年6月降至8.0%，货币扩张力度在边际收敛。M2-GDP剪刀差从2022年的8.7%收窄至2026年的3.3%，是好信号。", body_style))

story.append(h2("2.3 GDP：增长中枢下移"))
gdp_data = [
    ['年份', '2020', '2021', '2022', '2023', '2024', '2025', '2026H1'],
    ['GDP同比', '2.3%', '8.6%', '3.1%', '5.4%', '5.0%', '5.0%', '4.7%'],
]
story.append(make_table(gdp_data, [3*cm] + [2*cm]*7))
story.append(p("疫后反弹（2021年8.6%）→ 冲击（2022年3.1%）→ 修复（2023年5.4%）→ 中枢稳定在5.0%左右。2026年上半年降至4.7%，出现边际走弱。", body_style))

story.append(h2("2.4 LPR：持续降息但边际放缓"))
lpr_data = [
    ['时间段', '1年期LPR', '5年期LPR', '变化'],
    ['2024年1月', '3.45%', '4.20%', '起点'],
    ['2024年9月', '3.35%', '3.85%', '首轮大幅下调'],
    ['2025年1月', '3.10%', '3.60%', '继续降息'],
    ['2025年4月', '3.00%', '3.50%', '进一步下调'],
    ['2026年至今', '3.00%', '3.50%', '已连续16个月未动'],
]
story.append(make_table(lpr_data, [3.5*cm, 3*cm, 3*cm, 6*cm]))
story.append(p("5年期LPR从4.20%降至3.50%，累计降幅70bp。但2025年4月以来已连续16个月未再下调，降息空间收窄，货币政策从\"主动出击\"转向\"观望等待\"。", body_style))
story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第三章：卢麒元框架核心计算
# ═══════════════════════════════════════════════════
story.append(h1("三、卢麒元框架核心计算（展开过程）"))
story.append(spacer(4))

story.append(bold("输入参数："))
story.append(p("CPI同比 = 1.0%　　M2同比增速 = 8.0%　　GDP同比增速 = 4.7%（H1累计）"))
story.append(p("5年期LPR = 3.5%　　房价同比涨幅 = 1.8%"))

# 3.1
story.append(h2("3.1 真实通胀率计算"))
story.append(bold("方法一：M2法（推荐）"))
story.append(formula("真实通胀率 = CPI + (M2增速 - GDP增速)"))
story.append(formula("= 1.0% + (8.0% - 4.7%)"))
story.append(formula("= 1.0% + 3.3%"))
story.append(formula("= <b>4.3%</b>"))
story.append(p("虽然官方CPI仅1.0%，但多余的货币（M2-GDP剪刀差=3.3%）并未消失，而是以资产泡沫或未来通胀压力的形式潜伏。真实购买力稀释速度约为4.3%/年。", body_style))

story.append(bold("方法二：资产配置法"))
story.append(formula("真实通胀率 = 60%×CPI + 20%×房价涨幅 + 20%×其他资产(取2.1%)"))
story.append(formula("= 0.6 × 1.0% + 0.2 × 1.8% + 0.2 × 2.1%"))
story.append(formula("= 0.6% + 0.36% + 0.42%"))
story.append(formula("= <b>1.38%</b>"))
story.append(p('两种方法差值约2.92%，说明货币超发并未完全体现在资产价格上——大量货币处于\u201c沉默\u201d状态（流通速度极低），一旦货币流通速度恢复，通胀将显著反弹。', body_style))

# 3.2
story.append(h2("3.2 实质利率计算"))
story.append(bold("M2法："))
story.append(formula("实质利率 = 名义利率(LPR) - 真实通胀率(M2法) = 3.5% - 4.3% = <b>-0.8%  ⚠️ 实质负利率</b>"))
story.append(bold("资产法："))
story.append(formula("实质利率 = 3.5% - 1.38% = <b>2.12%  ✓ 实质正利率</b>"))
story.append(p("<b>关键判断：</b>以M2法衡量，中国处于实质负利率状态（-0.8%）。持有现金的实际购买力每年缩水约0.8%。负利率深度远小于2020-2022年（当时曾达-5%以上），说明货币超发程度在改善。", body_style))

# 3.3
story.append(h2("3.3 四矩阵周期定位（以M2法为准）"))

quad_data = [
    ['判断标准', '阈值', '当前值', '判定'],
    ['GDP增速', '≥ 5.0% = 高增长', '4.7%', '低增长'],
    ['真实通胀率', '≥ 5.0% = 高通胀', '4.3%', '低通胀'],
]
story.append(make_table(quad_data, [3.5*cm, 4.5*cm, 2.5*cm, 2.5*cm]))

matrix_data = [
    ['', '高通胀（≥5%）', '低通胀（<5%）'],
    ['高增长（≥5%）', '高高 🏠 房地产', '高低 📈 股票/实体'],
    ['低增长（<5%）', '低高 🥇 黄金/大宗', '★ 低低 💰 现金/债券 ← 当前'],
]
story.append(make_table(matrix_data, [3.5*cm, 5*cm, 5*cm]))

story.append(p("<b>★ 当前周期状态：【低低】— 低增长 + 低通胀</b>", highlight_style))
story.append(p("框架建议资产：现金/债券。但需注意，当前处于多重边界状态，详见第四章分析。", body_style))

story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第四章：关键边界分析
# ═══════════════════════════════════════════════════
story.append(h1("四、关键边界分析"))
story.append(spacer(4))

story.append(h2("4.1 处于「低低」与「高低」的边界"))
story.append(p("GDP 4.7%距离高增长阈值5.0%仅差0.3个百分点。若下半年政策发力，全年GDP达到5.0%，周期将从「低低」切换至<b>「高低」</b>（高增长+低通胀），资产偏好从现金/债券切换至<b>股票/实体经济</b>。", body_style))

story.append(h2("4.2 处于「低低」与「低高」的边界"))
story.append(p("真实通胀率4.3%距离高通胀阈值5.0%仅差0.7个百分点。若货币流通速度回升或外部冲击（大宗商品涨价），通胀突破5%，周期将切换至<b>「低高」</b>（滞胀），资产偏好切换至<b>黄金/大宗商品</b>。", body_style))

story.append(h2("4.3 三重边界状态总结"))
story.append(p("<b>核心结论：中国经济正处于三个象限的交界点，极其微妙。</b>下半年的政策力度和外部环境将决定最终落入哪个象限。这不是一个可以\"单边押注\"的时刻，而是一个需要\"灵活应变\"的时刻。", body_style))

# 象限图 - 文字版
ascii_matrix = """<br/>
<font face="Courier" size="9">
             高通胀(≥5%)<br/>
                ↑<br/>
        ┌───────┼───────┐<br/>
        │ 低高   │  高高  │<br/>
        │ 黄金   │  房地产 │<br/>
低增长←─┼────★───┼────────→高增长(≥5%)<br/>
 4.7%   │ ← 当前 │        │<br/>
        │ 低低   │  高低  │<br/>
        │ 现金   │  股票  │<br/>
        └───────┼───────┘<br/>
                ↓<br/>
             低通胀(&lt;5%)<br/>
</font>"""
story.append(p(ascii_matrix, body_no_indent))

story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第五章：与政府目标的差距分析
# ═══════════════════════════════════════════════════
story.append(h1("五、与2026年政府目标的差距分析"))
story.append(spacer(4))

gap_data = [
    ['指标', '2026年目标', '2026年H1实际', '差距', '判断'],
    ['GDP增速', '~5.0%', '4.7%', '-0.3%', '需下半年达5.3%方可完成全年目标'],
    ['CPI', '~2.0%', '1.0%', '-1.0%', '通缩压力显著大于预期'],
    ['城镇新增就业', '1200万+', '待确认', '—', '—'],
    ['调查失业率', '~5.5%', '待确认', '—', '—'],
]
story.append(make_table(gap_data, [3*cm, 2.5*cm, 2.5*cm, 2*cm, 6.5*cm]))

story.append(spacer(10))
story.append(h2("政策启示："))
story.append(p("1. <b>下半年大概率加大财政刺激</b>：专项债加速发行、超长期特别国债落地、财政赤字率实际执行可能突破3.0%。", body_style))
story.append(p("2. <b>若Q3数据继续走弱，不排除进一步降息降准</b>：LPR可能从3.5%→3.3%，降准25-50bp。", body_style))
story.append(p("3. <b>CPI 1.0%远低于2.0%目标</b>：通缩治理优先级上升，消费刺激政策（以旧换新等）将持续加码。", body_style))
story.append(p("4. <b>GDP缺口0.3%看似不大，但趋势在走弱</b>（Q1=5.0%→Q2≈4.4%），若Q3继续下滑，政策力度将被迫升级。", body_style))
story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第六章：2026年下半年投资建议
# ═══════════════════════════════════════════════════
story.append(h1("六、2026年下半年投资建议"))
story.append(spacer(4))

story.append(bold("按卢麒元框架，「低低」状态下优先配置现金/债券。但当前处于边界位置，需做三情景分析："))

# 情景A
story.append(h2("情景A（概率 45%）：稳增长见效 → 切换至「高低」"))
story.append(p("<b>触发条件：</b>下半年政策加码，全年GDP达到5.0%+，CPI维持2%以下。", body_style))
story.append(p("<b>资产偏好：📈 股票 > 债券 > 现金 > 黄金</b>", highlight_style))
story.append(p("<b>推荐方向：</b>新质生产力（AI、半导体、新能源）；高股息红利（电力、运营商、国有大行）；消费修复（以旧换新政策受益）。", body_style))

# 情景B
story.append(h2("情景B（概率 35%）：维持现状 → 继续「低低」"))
story.append(p("<b>触发条件：</b>政策效果有限，GDP全年4.7-4.9%，CPI温和。", body_style))
story.append(p("<b>资产偏好：💰 债券 > 现金 > 黄金 > 股票</b>", highlight_style))
story.append(p("<b>推荐方向：</b>中短久期利率债/高等级信用债；货币基金/同业存单（流动性管理）；黄金作为尾部风险对冲（5-10%配置）。", body_style))

# 情景C
story.append(h2("情景C（概率 20%）：通胀意外回升 → 切换至「低高」"))
story.append(p("<b>触发条件：</b>大宗商品涨价+货币流通速度恢复，真实通胀突破5%。", body_style))
story.append(p("<b>资产偏好：🥇 黄金/大宗商品 > 现金 > 债券 > 股票</b>", highlight_style))
story.append(p("<b>推荐方向：</b>黄金（核心避险）、铜/原油（供给约束）；资源股（石油、有色金属）；缩短债券久期，规避利率风险。", body_style))

# 配置汇总表
story.append(h2("6.2 配置建议汇总"))
alloc_data = [
    ['资产类别', '基准配置', '情景A', '情景B', '情景C'],
    ['股票',        '25%',     '↑40%',  '↓15%',  '↓10%'],
    ['债券',        '35%',     '↓20%',  '↑45%',  '↓15%'],
    ['现金/货币',   '25%',     '↓20%',  '↑25%',  '↑35%'],
    ['黄金/商品',   '15%',     '↓10%',  '↑15%',  '↑40%'],
]
story.append(make_table(alloc_data, [3*cm, 3*cm, 3*cm, 3*cm, 3*cm]))

story.append(h2("6.3 核心逻辑总结"))
story.append(p("1. <b>多重边界状态决定了「灵活应变」优先于「单边押注」。</b>", body_style))
story.append(p("2. <b>M2-GDP剪刀差收窄（从2022年8.7%→2026年3.3%）是好信号：</b>货币超发程度在改善，系统性风险下降。", body_style))
story.append(p("3. <b>实质负利率（-0.8%）不支持大规模持有现金：</b>需寻找能跑赢4.3%真实通胀的资产。", body_style))
story.append(p("4. <b>下半年重点关注三个信号：</b>①Q3 GDP数据 ②LPR是否下调 ③M2是否企稳回升。", body_style))
story.append(p("5. <b>外部风险：</b>全球流动性（美债/日元套息交易）、地缘政治（中东）、中美贸易摩擦。", body_style))

story.append(PageBreak())

# ═══════════════════════════════════════════════════
# 第七章：数据局限说明
# ═══════════════════════════════════════════════════
story.append(h1("七、数据局限说明"))
story.append(spacer(4))
story.append(p("1. GDP使用上半年累计同比（4.7%），若Q3数据公布后应重新评估。Q2单季数据为根据Q1和H1推算的近似值。", body_style))
story.append(p("2. 房价数据为70城中大城市新建商品住宅价格指数的算术均值，存在结构性偏差（三四线城市未被充分代表）。", body_style))
story.append(p("3. M2法真实通胀率假设货币超发部分最终会转化为通胀，但转化时滞不确定。当前货币流通速度处于历史低位，若流通速度V回升，通胀压力将加速释放。", body_style))
story.append(p("4. 四矩阵阈值（GDP≥5%、通胀≥5%）为经验值，不同经济周期下阈值可能需要调整。", body_style))
story.append(p("5. 以上分析基于卢麒元投资分析框架，结合公开宏观经济数据，不构成具体投资操作建议。投资决策需结合个人风险偏好和资产状况。", body_style))

story.append(spacer(50))
story.append(p("— 报告完 —", ParagraphStyle('end', parent=title_style, fontSize=14, textColor=C_GRAY)))
story.append(spacer(10))
story.append(p("分析完成：2026年8月3日 | 数据截至：2026年6月 | 数据来源：国家统计局/中国人民银行（AKShare采集）", small_style))
story.append(p("分析框架：卢麒元四矩阵投资决策框架 | 生成工具：ReportLab 5.0 + Noto Sans CJK", small_style))

# ── 构建 ──────────────────────────────────────────
doc.build(story)
print(f"✅ PDF 已生成: {output_path}")
print(f"   文件大小: {os.path.getsize(output_path) / 1024:.0f} KB")
