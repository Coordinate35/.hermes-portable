#!/usr/bin/env python3
"""生成《Kimi 金融行业 AI 解决方案》发布材料 PDF（2026-09-17）"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ── 中文字体 ──
pdfmetrics.registerFont(TTFont('CJK', "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))
pdfmetrics.registerFont(TTFont('CJK-Bold', "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))
FONT, FONT_B = 'CJK', 'CJK-Bold'

# ── 颜色 ──
C_DARK   = HexColor('#1a1a2e')
C_ACCENT = HexColor('#16213e')
C_BLUE   = HexColor('#0f3460')
C_RED    = HexColor('#e94560')
C_GOLD   = HexColor('#f5a623')
C_GREEN  = HexColor('#27ae60')
C_GRAY   = HexColor('#7f8c8d')
C_LIGHT  = HexColor('#f8f9fa')
C_BORDER = HexColor('#dee2e6')

output_path = "/home/coordinate35/hermes_data/kimi_finance_solution/Kimi金融行业解决方案_发布材料_20260917.pdf"
doc = SimpleDocTemplate(output_path, pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('T', fontSize=21, fontName=FONT_B, textColor=C_DARK,
    spaceAfter=6, alignment=TA_CENTER, leading=30)
subtitle_style = ParagraphStyle('S', fontSize=11, fontName=FONT, textColor=C_GRAY,
    spaceAfter=10, alignment=TA_CENTER, leading=16)
h1_style = ParagraphStyle('H1', fontSize=15, fontName=FONT_B, textColor=C_BLUE,
    spaceBefore=18, spaceAfter=9, leading=21)
h2_style = ParagraphStyle('H2', fontSize=12.5, fontName=FONT_B, textColor=C_ACCENT,
    spaceBefore=12, spaceAfter=7, leading=17)
body_style = ParagraphStyle('B', fontSize=10.5, fontName=FONT, textColor=black,
    leading=17, spaceAfter=5, alignment=TA_JUSTIFY)
body_ni = ParagraphStyle('BNI', parent=body_style, firstLineIndent=0)
small_style = ParagraphStyle('SM', fontSize=8.5, fontName=FONT, textColor=C_GRAY,
    leading=13, spaceAfter=3)
highlight_style = ParagraphStyle('HL', fontSize=10.5, fontName=FONT_B, textColor=C_RED,
    leading=17, spaceAfter=5)
li_style = ParagraphStyle('LI', parent=body_style, leftIndent=12, firstLineIndent=-12, spaceAfter=3)

def h1(t): return Paragraph(t, h1_style)
def h2(t): return Paragraph(t, h2_style)
def p(t, s=body_style): return Paragraph(t, s)
def li(t): return Paragraph(f"• {t}", li_style)
def sp(h=6): return Spacer(1, h)

def make_table(data, col_widths, header_rows=1, font_size=9):
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    cmds = [
        ('BACKGROUND', (0, 0), (-1, header_rows-1), C_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, header_rows-1), white),
        ('FONTNAME', (0, 0), (-1, header_rows-1), FONT_B),
        ('FONTSIZE', (0, 0), (-1, header_rows-1), font_size),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, header_rows), (-1, -1), FONT),
        ('FONTSIZE', (0, header_rows), (-1, -1), font_size),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, header_rows), (-1, -1), [white, C_LIGHT]),
    ]
    t.setStyle(TableStyle(cmds))
    return t

story = []

# ════════ 封面 ════════
story.append(sp(70))
story.append(p("月之暗面 · Moonshot AI", ParagraphStyle('X', parent=subtitle_style, fontSize=12)))
story.append(p("Kimi 金融行业 AI 解决方案", title_style))
story.append(p("发布材料整理", ParagraphStyle('X', parent=title_style, fontSize=15, textColor=C_RED)))
story.append(sp(18))
story.append(p("发布时间：2026年9月17日", subtitle_style))
story.append(p("涵盖 10+ 权威数据源 · 9 项金融技能 · 5 项安全合规措施", subtitle_style))
story.append(p("资料来源：Kimi 官方博客 / 官方解决方案页 / 金色财经快讯", subtitle_style))
story.append(PageBreak())

# ════════ 一、发布要点 ════════
story.append(h1("一、发布要点"))
story.append(p("2026年9月17日，月之暗面正式发布「Kimi 金融行业 AI 解决方案」。该方案整合 Kimi 面向金融行业的模型、产品与能力，核心构成四大模块："))
story.append(sp(4))
summary = [
    ['模块', '内容'],
    ['10+ 权威数据源', '一站式接入即时可靠的金融数据（万得、东方财富、标普全球、同花顺 iFinD、财联社、财新数据等）'],
    ['9 项金融技能', '将金融工作关键环节封装为专业技能（Skill），沉淀专业金融工作流'],
    ['5 项合规安全措施', '通过「风险评估网关」实现：分类分级、个人信息保护、访问授权、核验复核、审计追溯'],
    ['机构级交付能力', '数据建模与报告交付，产出可编辑的 Excel 模型、PPT 报告和 Word 材料'],
]
story.append(make_table(summary, [3.6*cm, 13.4*cm], font_size=9.5))
story.append(sp(8))
story.append(p("方案将数据获取、专业分析与成果交付连接起来，覆盖从持仓早报、财报点评，到项目筛选、深度研究和组合复盘的工作流。在已落地的机构合作中，过去以“天”计的资料处理和初稿制作被压缩到“小时”级。", body_style))
story.append(h2("应用形态（能力已全量上线）"))
story.append(li("<b>个人用户</b>：在 kimi.com 安装体验金融技能与数据源插件"))
story.append(li("<b>团队用户</b>：在 Kimi Work 桌面端、Kimi Code 安装调用数据源插件、金融技能，体验自定义插件和电脑本地 Agent 能力"))
story.append(li("<b>机构用户</b>：Kimi 托管智能体（Kimi Hosted Agents）服务，为智能体进入真实业务流程提供可配置、可审计的运行环境"))
story.append(PageBreak())

# ════════ 二、业务背景 ════════
story.append(h1("二、业务背景（官方表述）"))
story.append(p("金融是数据与信息最为密集的行业之一。行业生产力长期受限于两个要素：<b>数据处理的速度</b>和<b>信息搜集的广度</b>。"))
story.append(li("<b>时效性挑战</b>：分析师的信息来源主要是公告、新闻和研报，过去一份研究结论往往要一天才能整理出来；而现在市场要求分钟级的响应，全球市场结构的变化需要被即时吸收。"))
story.append(li("<b>信息碎片化</b>：关键数据散落在财报、法律文件、研报和公告中，专业人员需要花大量时间完成数据查询、比对和整理，再去进行分析工作。"))
story.append(sp(6))
story.append(p("2026 年，随着大模型推理与工具调用能力的提升，AI 正在从单点辅助走向完整金融工作流的端到端交付：<b>理解工作目标，搜索专业数据，执行分析与建模，并做成机构级的交付成果</b>。金融行业对准确性和合规性要求极高，AI 的输出必须结构专业、来源清晰、便于核查，才能真正进入业务流程。", body_style))

# ════════ 三、数据源 ════════
story.append(h1("三、10+ 权威数据源"))
story.append(p("Kimi 全套产品（网页版 kimi.com、桌面端 Kimi Work、Kimi Code）内置以下数据源，通过 MCP 直接接入研究任务，关键数字可以回到原始出处核对："))
story.append(h2("金融数据"))
story.append(make_table([
    ['数据源', '说明'],
    ['Wind 万得', '「Wind Alice 万得金融数据服务」插件（万得首席战略官葛正琦证言）'],
    ['东方财富', '「妙想金融数据」插件，可调用 14 项金融研究能力'],
    ['标普全球 S&P Global', '全球金融数据'],
    ['同花顺 iFinD', '行情与财务数据'],
    ['财联社 / 财新数据 / 新华财经', '财经新闻与资讯'],
    ['恒生聚源 / Crunchbase', '金融数据 / 未上市公司数据'],
], [5.4*cm, 11.6*cm], font_size=9))
story.append(sp(6))
story.append(h2("企业与合规 / 其他能力"))
story.append(li("<b>天眼查</b>：工商、司法信息补充；<b>元典法律</b>：知识产权及法规信息"))
story.append(li("<b>Scholar</b>：学术论文全文检索"))
story.append(li("<b>Office 产物生成</b>：Word、Excel、PDF 等格式；图片和语音生成工具"))
story.append(li("<b>Kimi 浏览器扩展</b>（前身 Kimi WebBridge）与 <b>Computer Use</b>：授权下让 Agent 使用浏览器和本机桌面应用，没有 API 的系统也能接入工作流"))
story.append(li("<b>金融投研套件</b>：覆盖二级投研、一级 deal 全流程与企业财务关账"))
story.append(li("<b>Cloudflare 开发者工具</b>：2500+ 官方 API 端点，支撑定制与集成"))
story.append(p("官方表示正在推进与飞书、腾讯文档、WPS 等中文办公系统的连接。", small_style))
story.append(PageBreak())

# ════════ 四、9 项金融技能 ════════
story.append(h1("四、9 项金融技能（Skill）"))
story.append(p("Kimi 与一线机构分析师、基金经理和投行团队合作，将金融工作的关键环节封装为 9 个专业技能，每个技能对应一类有稳定分析步骤和交付标准的工作："))
story.append(make_table([
    ['#', '技能名称', '对应工作'],
    ['1', '机构财务建模', '搭建财务模型，输出可调假设的 Excel 模型与可比公司估值表'],
    ['2', '机构研究报告', '机构级深度研究报告'],
    ['3', '机构 PPT（机构研究演示文稿）', '投决汇报材料制作'],
    ['4', '金融动态图表', '机构级金融交互图表（标注、切换类型、编辑数据）'],
    ['5', '业绩点评', '财报业绩点评'],
    ['6', '一致预期地图', '市场一致预期梳理'],
    ['7', '组合复盘', '持仓组合复盘'],
    ['8', '持仓早报', '每日持仓简报'],
    ['9', 'HK IPO 透镜（港股上市透视镜）', '港股 IPO 项目透视'],
], [0.9*cm, 6.1*cm, 10.0*cm], font_size=9))
story.append(sp(8))
story.append(h2("配套通用能力"))
story.append(li("<b>灵动报告</b>：将卖方深度研究转化为可交互 HTML 可视化报告，用于研究营销、客户沟通与公开发布"))
story.append(li("<b>看板 / 组件</b>：Kimi Work 中搭建金融终端看板，专业信源、组合持仓和覆盖公司关联展示"))
story.append(li("<b>圈画功能</b>：机构级图表上直接标注、编辑（CAGR 与差值标注、图表类型切换、修改标签、编辑数据）"))
story.append(li("<b>自定义插件（Plugin Builder）</b>：自然语言描述系统与流程，按 MCP、API 或浏览器技能三条路径创建自定义插件"))
story.append(PageBreak())

# ════════ 五、案例与效率数据 ════════
story.append(h1("五、真实案例与效率数据（案例已脱敏）"))
story.append(make_table([
    ['场景', '技能', '效率提升'],
    ['投资银行 / 私募股权：\n财务建模', '机构财务建模', '人力投入由 5–7 人天\n降至 0.5–1 人天'],
    ['行业研究：深度研究', '机构研究报告', '研究周期从 10–20 天\n缩短至约 2 天'],
    ['商业银行：授信报告', '（招股书+调研纪要+征信）', '单户材料准备效率\n提升 5 倍以上'],
    ['保险：宠物险分析报告', '机构 PPT', '21 页投决材料，人力投入由\n7–10 人天降至约 2 人天'],
], [4.4*cm, 5.0*cm, 7.6*cm], font_size=9))
story.append(sp(10))
story.append(h2("中信建投证券试点案例（首个「风险评估网关」验证）"))
story.append(p("中信建投证券将<b>临时受托报告生成</b>作为首个验证场景，基于 Kimi 托管智能体构建「临时受托报告生成」智能体，并接入内部业务系统。首轮验证覆盖发行人公告内容识别、受托管理债券筛选及报告初稿生成等环节，保留业务人员的复核与决策职责。"))
story.append(make_table([
    ['维度', '数据'],
    ['覆盖范围', '50 余家发行人、100 余只存续公司债券、60 余份临时受托管理事务报告'],
    ['系统接入周期', '原计划 2 个月 → 实际 3 个工作日'],
    ['单份报告人工时间', '约 30 分钟 → 10 分钟（人工投入下降 67%）'],
    ['可复用性', '网关跨场景复用，新场景沿用同一套合规检查机制完成接入与上线评审'],
], [4.2*cm, 12.8*cm], font_size=9))
story.append(sp(6))
story.append(p("<b>中信建投证券首席信息官肖钢</b>：数据安全是首要门槛，Kimi 承诺企业数据零留存、不用于训练，托管智能体平台与风险评估网关支持模型安全接入真实业务流程。", body_style))
story.append(PageBreak())

# ════════ 六、5 项安全合规措施 ════════
story.append(h1("六、5 项安全合规措施（风险评估网关）"))
story.append(p("围绕“哪些信息可以传给外部模型、数据源和工具访问是否经过授权、输出是否有据可查、执行过程能否追溯”，Kimi 与中信建投证券共建「风险评估网关」，将合规要求落实为 5 项具体措施："))
story.append(sp(4))
comp = [
    ['措施', '内容'],
    ['1 数据分类分级', '依据机构制度明确不同敏感等级数据的使用和外发边界，网关按规则检查任务、附件及工具返回内容'],
    ['2 个人信息保护', '遵循最小必要原则，对个人信息按规则过滤、脱敏或拦截，仅向模型传递任务必需且获准使用的内容'],
    ['3 数据源与工具访问授权', '将授权要求落实到每次调用，拦截未经授权的数据查询或工具操作，并检查返回内容'],
    ['4 生成内容核验与人工复核', '输出标注来源、时间和待核实事项，支持回查依据；初步材料经业务人员复核，不直接形成立项结论'],
    ['5 审计与责任追溯', '任务、数据来源、处理决定和工具调用记录关联保存，支持按任务回查执行过程'],
]
story.append(make_table(comp, [4.4*cm, 12.6*cm], font_size=9))

# ════════ 七、客户与证言 ════════
story.append(h1("七、客户与证言（官方披露）"))
story.append(p("<b>已服务客户（部分）</b>：中金公司、中信建投证券、国寿股权、易方达基金、汇添富基金、人保资本、蚂蚁集团、美团、Alpha派、熵简科技、红杉中国、MONOLITH、真格基金、五源资本、蓝驰创投、襄禾资本、IDG Capital、凯辉基金、正心谷资本、芯联资本、鼎晖百孚、北汽产业投资"))
story.append(sp(6))
story.append(make_table([
    ['机构 / 人物', '证言要点'],
    ['工商银行北京分行投资银行部', 'Kimi 让行业研究效率有质的提升'],
    ['易方达基金 CIO 刘硕凌', 'K3 已接入自研企业 AI 工作台 EWork'],
    ['汇添富基金 AI 首席创新官何丽峰', 'K3 长文本与长程 Agent 能力适配投研深度研究'],
    ['红杉中国 合伙人郑庆生', 'Kimi 深度研究提升投研与投后效率'],
    ['真格基金', '提升硬科技前沿领域研究效率、更早发掘潜在创业者'],
    ['蓝驰创投 管理合伙人朱天宇', '融入真实投资工作流；Deep Research 与专业数据源助力项目与行业研究'],
    ['万得 首席战略官葛正琦', 'Kimi 与 Wind 上线「Wind Alice 万得金融数据服务」插件'],
    ['讯兔科技 首席科学家刘广文', 'K3 金融分析能力与 iRaB 投研 benchmark 成绩'],
    ['熵简科技 CTO 李渔', 'K3 是能平替海外旗舰模型的国产大模型'],
], [5.2*cm, 11.8*cm], font_size=9))
story.append(PageBreak())

# ════════ 八、官方链接与时间线 ════════
story.append(h1("八、官方链接"))
story.append(li("官方博客《Kimi 发布金融行业 AI 解决方案》：https://www.kimi.com/zh-cn/news/kimi-financial-industry-ai-solution"))
story.append(li("官方解决方案页：https://www.kimi.com/zh-cn/solutions/financial-services"))
story.append(li("企业合作（Kimi 托管智能体 / 定制化 Skills / 专属数据接入）：platform.kimi.com/contact-sales"))
story.append(sp(10))
story.append(h1("九、相关背景时间线（供参考）"))
story.append(make_table([
    ['时间', '事件'],
    ['2026-04', 'Kimi 接入同花顺 iFinD、天眼查等专业金融数据库（媒体：财联社等）'],
    ['2026-06', 'Kimi Work Beta 上线，内置金融专业数据库（媒体：36氪等）'],
    ['2026-07', 'Kimi K3 发布（2.8万亿参数、100万 token 上下文），金融行业机构合作推进'],
    ['2026-09-10', 'Kimi 企业合作伙伴计划启动（与 IT 服务商、集成商共建 FDE 队伍）'],
    ['2026-09-17', 'Kimi 金融行业 AI 解决方案正式发布'],
], [3.0*cm, 14.0*cm], font_size=9))
story.append(sp(14))
story.append(p("— 材料完 —", ParagraphStyle('E', parent=title_style, fontSize=13, textColor=C_GRAY)))
story.append(sp(8))
story.append(p("整理：Hermes（2026-09-17）｜资料来源：Kimi 官方博客、Kimi 官方解决方案页、金色财经快讯；本材料为公开发布信息整理，未经官方审阅。", small_style))

doc.build(story)
print(f"PDF 已生成: {output_path}")
print(f"文件大小: {os.path.getsize(output_path)/1024:.0f} KB")
