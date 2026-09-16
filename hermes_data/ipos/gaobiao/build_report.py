#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高标科技宏观压力测试报告生成器
输出: 高标科技压力测试报告_20260916.md / .pdf （同目录）
用法: python3 build_report.py [--md-only]
数据: 招股说明书(申报稿, 2026-06-18 受理; 报告期 2023-2025)
模型: ~/hermes_data/ipos/gaobiao/scenario_model.py (同式重算, 参数可调)
"""
import os
import sys
import html

OUT_DIR = "/home/coordinate35/hermes_data/ipos/gaobiao"
BASE = "高标科技压力测试报告_20260916_v2"
MD_PATH = os.path.join(OUT_DIR, BASE + ".md")
PDF_PATH = os.path.join(OUT_DIR, BASE + ".pdf")
MD_ONLY = "--md-only" in sys.argv

# ---------------- 1) 模型重算（与 scenario_model.py 同式） ----------------
M0   = 127224.91 / 1e4      # 直接材料 12.7225 亿
R0   = 205189.07 / 1e4      # 主营收入 20.5189 亿
C0   = 154739.48 / 1e4      # 主营成本 15.4739 亿
G0   = R0 - C0              # 主营毛利 5.045 亿
PBT0 = 2.07589              # 利润总额 2.0759 亿
NP0  = 1.81739              # 净利润 1.8174 亿
TAX  = 1 - NP0 / PBT0       # 有效税率 12.45%
E0   = 1.66801              # 境外收入 1.668 亿
EXP0 = (5854.75 + 13468.29 + 8937.72 + 474.60) / 1e4  # 期间费用 2.8735 亿
LAM  = M0 / R0              # 材料/收入 = 62.0%


def scen(m, k, fx, q, ex):
    dG   = -(1 - k) * m * M0
    dFx  = fx * E0
    dVol = q * G0
    dExp = ex * EXP0
    pbt2 = PBT0 + dG + dFx + dVol - dExp
    np2  = pbt2 * (1 - TAX)
    r2   = R0 * (1 + k * LAM * m)
    g2   = G0 + dG
    return dict(m=m, k=k, dG=dG, dFx=dFx, dVol=dVol, dExp=dExp,
                R2=r2, G2=g2, gm2=g2 / r2 * 100, pbt2=pbt2, np2=np2)


S1  = scen(0.25, 0.65, -0.05,  0.00, 0.10)
S2  = scen(0.45, 0.50, -0.10, -0.05, 0.20)
S3  = scen(0.70, 0.45, -0.30, -0.12, 0.30)
S2F = scen(0.45, 0.80, -0.10, -0.05, 0.20)

# S2 条件下打平临界 k*
dG_need = -(PBT0 + S2['dFx'] + S2['dVol'] - S2['dExp'])
K_STAR = 1 + dG_need / (S2['m'] * M0)
# S3（极端）条件下打平临界 k*
dG_need3 = -(PBT0 + S3['dFx'] + S3['dVol'] - S3['dExp'])
K_STAR3 = 1 + dG_need3 / (S3['m'] * M0)

# 双阈值表
KS = [0, 0.3, 0.5, 0.65, 0.7, 0.8]
THR = [(k, PBT0 / ((1 - k) * M0) * 100, G0 / ((1 - k) * M0) * 100) for k in KS]

# 材料 +10% 敏感度（净利口径）
SENS = [(k, (1 - k) * 0.10 * M0 * (1 - TAX) / NP0 * 100) for k in (0, 0.5, 0.7)]

# 单位经济：m=45% 所需提价换算
DP45 = 45.23 * LAM * 0.45           # 元/台
DP45_SHARE = DP45 / 2500 * 100      # 占整车零售价 %

# 名义 vs 实际（累计通胀 40%）
REAL_G = G0 / 1.4


def f2(x):
    return f"{x:.2f}"


def sgn(x):
    return f"{x:+.2f}" if abs(x) >= 0.005 else "0.00"


def pct0(x):
    return f"{x:+.0f}%"


def np_label(s):
    return "（亏损）" if s['np2'] < 0 else f"（{pct0((s['np2'] / NP0 - 1) * 100)}）"


# ---------------- 2) 报告内容（blocks: 单一来源，MD/PDF 共用） ----------------
blocks = []
blocks.append(("title", "高标科技压力测试报告"))
blocks.append(("meta", "广东高标智能科技股份有限公司（创业板 IPO 在审）｜美元重置·油价冲击情景定量测算"))
blocks.append(("meta", "日期：2026-09-16 ｜ 数据来源：招股说明书（申报稿，2026-06-18 受理；财务报告期 2023-2025）"))
blocks.append(("meta", "版本：v2（2026-09-16 修订）｜ 主要修订：极端情景汇率假设调整至约 1:5（详见假设）。"))
blocks.append(("meta", "模型：~/hermes_data/ipos/gaobiao/scenario_model.py（参数可调、可重跑）｜ 声明：本报告为压力测试，非盈利预测。"))

blocks.append(("h1", "一、事实（已发生、可核验）"))
blocks.append(("bullets", [
    "业务：短交通智能控制器占主营收入 91.7%（全球市占率 20.7%，第一；均价 45.23 元/台）；E-bike 电驱系统 7.6%；机器人运控组件 0.7%。境外收入占 8.13%（欧元、美元结算）。",
    f"2025 年经营基准：主营收入 {f2(R0)} 亿元；直接材料 {f2(M0)} 亿元（占收入 {LAM*100:.1f}%、占主营成本 82.2%）；主营毛利 {f2(G0)} 亿元（毛利率 {G0/R0*100:.2f}%）；期间费用 {f2(EXP0)} 亿元；利润总额 {f2(PBT0)} 亿元；净利润 {f2(NP0)} 亿元（有效税率 {TAX*100:.2f}%）。",
    "招股书自带敏感性：材料价格 ±10% → 主营成本 ±8.2%、主营毛利 25.2%（反向）。",
    "历史价格行为：2024 年行业“以价换量”，公司控制器均价跟随下降 6.46%——降价传导有实证，提价传导无样本。",
    "客户结构：前五大客户占 65.55%（雅迪、爱玛、台铃、九号、小刀等整车厂）；B2B 零部件供应商，非整车/品牌商。",
    "缓冲：存货 3.31 亿元，约合 3.1 个月材料消耗（战略囤料的上限）。",
]))

blocks.append(("h1", "二、假设（外生输入，非预测）"))
blocks.append(("p", "情景设定（三档，含油价映射；全部为假设）："))
blocks.append(("table", {
    "header": ["情景", "油价情景", "材料涨幅 m", "提价传导 k", "人民币", "销量", "费用通胀"],
    "rows": [
        ["S1 温和", "$150-200", "+25%", "0.65", "升值 5%", "持平", "+10%"],
        ["S2 压力", "$200-250", "+45%", "0.50", "升值 10%", "-5%", "+20%"],
        ["S3 恶性", "$250-300", "+70%", "0.45", "升值 30%", "-12%", "+30%"],
    ],
    "widths": [2.9, 2.3, 2.4, 2.4, 2.3, 2.3, 2.3],
}))
blocks.append(("bullets", [
    "k 定义：实际提价 ÷ 维持毛利所需提价。因仅有 2024 年降价样本，上行传导按保守区间取值（0.45-0.65）。",
    "油价数值为压力情景口径（方向：美元重置下的能源重定价；数值为极端假设转述）。",
    "汇率假设：S1 / S2 为升值 5% / 10%；S3（极端）为升值 30%——对美元约 1:5（按 2025 年汇率中枢约 7.2 折算；截至 2026 年 9 月现汇约 6.7）。",
    "方法：线性外推（与招股书敏感性同法）；基准为 2025 静态口径、未含订单增长预期；未计入其他收益+投资收益（约 +0.2 亿元/年缓冲）、亏损情景未计税盾递延；销量影响以毛利近似边际贡献。",
]))

blocks.append(("h1", "三、推导过程"))
blocks.append(("p", f"① 材料杠杆：λ = {f2(M0)} / {f2(R0)} = {LAM*100:.1f}% —— 材料每涨 1%，需提价 {LAM:.2f}%（相对收入）才能保住毛利。"))
blocks.append(("p", f"② 毛利桥：ΔG = -(1-k) × m × {f2(M0)} 亿元。"))
blocks.append(("p", f"③ 平衡阈值：毛利归零 m* = {G0/M0*100:.1f}% / (1-k)；净利归零 m** = {PBT0/M0*100:.1f}% / (1-k)。"))
blocks.append(("p", f"④ 完整算例（S2）：材料 +45% → 成本 +5.72 亿元；所需提价 = {LAM*100:.1f}% × 45% = 27.9%；实际提价 = 0.50 × 27.9% = 13.95%；收入端 +2.86 亿元；ΔG = +2.86 - 5.72 = {sgn(S2['dG'])} 亿元。叠加汇率 {sgn(S2['dFx'])}、销量 {sgn(S2['dVol'])}、费用 {sgn(-S2['dExp'])}（亿元），利润总额 {f2(PBT0)} → {f2(S2['pbt2'])} 亿元，净利 {f2(S2['np2'])} 亿元。"))
blocks.append(("p", "⑤ 情景结果（亿元；收入/毛利为主营口径，净利为合并口径）："))
blocks.append(("table", {
    "header": ["情景", "收入", "毛利（毛利率）", "净利"],
    "rows": [
        ["S1 温和", f2(S1['R2']), f"{f2(S1['G2'])}（{S1['gm2']:.1f}%）", f"{f2(S1['np2'])}（{(S1['np2']/NP0-1)*100:+.0f}%）"],
        ["S2 压力", f2(S2['R2']), f"{f2(S2['G2'])}（{S2['gm2']:.1f}%）", f"{f2(S2['np2'])}{np_label(S2)}"],
        ["S3 恶性", f2(S3['R2']), f"{f2(S3['G2'])}（{S3['gm2']:.1f}%）", f"{f2(S3['np2'])}{np_label(S3)}"],
        ["反事实 S2·k=0.8", f2(S2F['R2']), f"{f2(S2F['G2'])}（{S2F['gm2']:.1f}%）", f"{f2(S2F['np2'])}（≈打平）"],
    ],
    "widths": [4.7, 3.3, 4.4, 4.6],
}))
blocks.append(("p", "损失拆解（亿元；对利润总额的影响）："))
blocks.append(("table", {
    "header": ["情景", "成本-提价", "汇率", "销量", "费用"],
    "rows": [
        ["S1 温和", sgn(S1['dG']), sgn(S1['dFx']), sgn(S1['dVol']), sgn(-S1['dExp'])],
        ["S2 压力", sgn(S2['dG']), sgn(S2['dFx']), sgn(S2['dVol']), sgn(-S2['dExp'])],
        ["S3 恶性", sgn(S3['dG']), sgn(S3['dFx']), sgn(S3['dVol']), sgn(-S3['dExp'])],
        ["反事实 S2·k=0.8", sgn(S2F['dG']), sgn(S2F['dFx']), sgn(S2F['dVol']), sgn(-S2F['dExp'])],
    ],
    "widths": [4.0, 3.3, 2.9, 2.9, 3.0],
}))

blocks.append(("h1", "四、结论"))
blocks.append(("bullets", [
    f"杀伤在成本端，不在需求端：{LAM*100:.1f}% 的材料杠杆是最大风险敞口；材料每涨 10%，净利减少约 {SENS[2][1]:.0f}% 至 {SENS[0][1]:.0f}%（视传导率 k）。",
    f"情景损失：温和情景净利 {f2(S1['np2'])} 亿元（-71%）；压力情景转亏 {f2(S2['np2'])} 亿元；恶性情景亏 {f2(S3['np2'])} 亿元。短期利润先受伤。",
    f"生死开关是提价传导率 k：修复至约 {K_STAR:.2f}（S2 条件下）即可打平；提价物理空间很小——S2 仅需 +{DP45:.1f} 元/台，约合整车零售价的 {DP45_SHARE:.2f}%。卡点是时滞与议价，不是空间。",
    f"名义 ≠ 实际：即使保住 {f2(G0)} 亿元名义毛利，累计通胀 40% 后实际购买力约 {f2(REAL_G)} 亿元（“货是货，币是币”）。",
    "判断：压力情景击穿利润，但不击穿商业逻辑；跟踪调价动作与季度毛利率即可观测翻转。",
]))

blocks.append(("h1", "五、临界点（何时发生变化）"))
blocks.append(("p", "① 双阈值表（材料涨幅达到该值时，先净利归零、再毛利归零）："))
blocks.append(("table", {
    "header": ["提价传导率 k", "净利归零 m**", "毛利归零 m*"],
    "rows": [[f"{k:g}", f"{m2:.1f}%", f"{m1:.1f}%"] for (k, m2, m1) in THR],
    "widths": [5.5, 5.75, 5.75],
}))
blocks.append(("bullets", [
    f"② 打平临界（S2 条件）：k* ≈ {K_STAR:.2f}（k=0.8 时净利 {f2(S2F['np2'])} 亿元）——传导率的开关点；极端情景（S3）下 k* ≈ {K_STAR3:.2f}。",
    "③ 情景切换触发：油价上破 $200 → S1 切 S2；上破 $250 → S2 切 S3。",
    "④ 时间缓冲：存货约 3.1 个月；战略囤料窗口 1-2 个季度。",
    "⑤ 观测锚：公司及同业（八方股份、安乃达）调价函；季度毛利率；布伦特油价；人民币汇率；材料采购价。",
]))
blocks.append(("p", "附注：全部外生假设（m/k/汇率/量/费用）可调，模型可重跑：python3 ~/hermes_data/ipos/gaobiao/scenario_model.py"))


# ---------------- 3) Markdown 输出 ----------------
def render_md(bl):
    lines = []
    for kind, data in bl:
        if kind == "title":
            lines.append(f"# {data}")
            lines.append("")
        elif kind == "meta":
            lines.append(f"> {data}")
            lines.append("")
        elif kind == "h1":
            lines.append(f"## {data}")
            lines.append("")
        elif kind == "p":
            lines.append(data)
            lines.append("")
        elif kind == "bullets":
            for it in data:
                lines.append(f"- {it}")
            lines.append("")
        elif kind == "table":
            lines.append("| " + " | ".join(data["header"]) + " |")
            lines.append("|" + "---|" * len(data["header"]))
            for r in data["rows"]:
                lines.append("| " + " | ".join(str(c) for c in r) + " |")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(render_md(blocks))
print("MD_OK:", MD_PATH)

if MD_ONLY:
    print("BUILD_OK (md only)")
    sys.exit(0)

# ---------------- 4) PDF 输出（reportlab） ----------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except Exception as e:  # noqa
    print("REPORTLAB_MISSING:", e)
    sys.exit(2)

TEST_CHARS = "高标科技压力测试临界点传导率情景推导结论±×≈→"


def try_font(name, paths):
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, p))
            face = pdfmetrics.getFont(name).face
            cmap = getattr(face, "charToGlyph", {}) or {}
            missing = [c for c in TEST_CHARS if ord(c) not in cmap]
            if missing:
                print(f"[font] skip {p}: missing {''.join(missing)}")
                continue
            print(f"[font] OK {p}")
            return name
        except Exception as e:
            print(f"[font] fail {p}: {e}")
            continue
    return None


FONT = try_font("CJK", [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
])
if not FONT:
    print("PDF_FONT_FAIL")
    sys.exit(3)
FONT_B = try_font("CJK-B", [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
]) or FONT


def pick_bullet():
    cmap = getattr(pdfmetrics.getFont(FONT).face, "charToGlyph", {}) or {}
    for c in "•·▪◦▸":
        if ord(c) in cmap:
            return c
    return ""


BULLET = pick_bullet()
print("[font] bullet =", repr(BULLET))

_face_map = getattr(pdfmetrics.getFont(FONT).face, "charToGlyph", {}) or {}
_all_texts = []
for _kind, _data in blocks:
    if _kind in ("title", "meta", "h1", "p"):
        _all_texts.append(_data)
    elif _kind == "bullets":
        _all_texts.extend(_data)
    elif _kind == "table":
        _all_texts.extend(_data["header"])
        _all_texts.extend(str(c) for _r in _data["rows"] for c in _r)
_miss = sorted({c for _t in _all_texts for c in _t if ord(c) > 127 and ord(c) not in _face_map})
print("[font] full-text missing:", _miss if _miss else "NONE")

TITLE = ParagraphStyle("t", fontName=FONT_B, fontSize=19, leading=26, alignment=1,
                       textColor=colors.HexColor("#1a1a1a"), spaceAfter=6)
META = ParagraphStyle("m", fontName=FONT, fontSize=8.5, leading=13,
                      textColor=colors.HexColor("#666666"), alignment=1, spaceAfter=2)
H1 = ParagraphStyle("h1", fontName=FONT_B, fontSize=13.5, leading=20,
                    textColor=colors.HexColor("#1f3b57"), spaceBefore=9, spaceAfter=4)
BODY = ParagraphStyle("b", fontName=FONT, fontSize=10, leading=15.5,
                      textColor=colors.HexColor("#222222"))
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=13, bulletIndent=2, spaceAfter=2)
CELL = ParagraphStyle("c", fontName=FONT, fontSize=8.5, leading=12)
CELLC = ParagraphStyle("cc", parent=CELL, alignment=1)
CELLH = ParagraphStyle("ch", parent=CELLC, textColor=colors.white)


def make_table(header, rows, widths):
    data = [[Paragraph(html.escape(str(h)), CELLH) for h in header]]
    for r in rows:
        data.append([Paragraph(html.escape(str(c)), CELL if i == 0 else CELLC)
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d2da")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def footer(canv, doc):
    canv.saveState()
    canv.setFont(FONT, 7.5)
    canv.setFillColor(colors.HexColor("#999999"))
    canv.drawCentredString(A4[0] / 2, 1.0 * cm, f"高标科技压力测试报告 · 2026-09-16 · 第 {doc.page} 页")
    canv.restoreState()


story = []
for kind, data in blocks:
    if kind == "title":
        story.append(Paragraph(html.escape(data), TITLE))
    elif kind == "meta":
        story.append(Paragraph(html.escape(data), META))
    elif kind == "h1":
        story.append(Paragraph(html.escape(data), H1))
    elif kind == "p":
        story.append(Paragraph(html.escape(data), BODY))
        story.append(Spacer(1, 3))
    elif kind == "bullets":
        for it in data:
            if BULLET:
                story.append(Paragraph(html.escape(it), BUL, bulletText=BULLET))
            else:
                story.append(Paragraph(html.escape(it), BUL))
        story.append(Spacer(1, 3))
    elif kind == "table":
        story.append(make_table(data["header"], data["rows"], data["widths"]))
        story.append(Spacer(1, 3))

doc = SimpleDocTemplate(PDF_PATH, pagesize=A4,
                        leftMargin=1.9 * cm, rightMargin=1.9 * cm,
                        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
                        title="高标科技压力测试报告", author="Hermes")
try:
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
except Exception as e:
    print("PDF_FAIL:", e)
    sys.exit(4)

print("PDF_OK:", PDF_PATH)
print("== 关键数值自检 ==")
print(f"lambda={LAM*100:.1f}%  G0={f2(G0)}  PBT0={f2(PBT0)}  TAX={TAX*100:.2f}%")
print(f"NP: S1={f2(S1['np2'])}  S2={f2(S2['np2'])}  S3={f2(S3['np2'])}  S2F={f2(S2F['np2'])}  K*={K_STAR:.3f}  K*3={K_STAR3:.3f}")
print("THR:", [(f"{k:g}", f"{m2:.1f}", f"{m1:.1f}") for (k, m2, m1) in THR])
print(f"SENS(+10%材料): k0=-{SENS[0][1]:.1f}%  k.5=-{SENS[1][1]:.1f}%  k.7=-{SENS[2][1]:.1f}%")
print(f"DP45={DP45:.1f}元/台  整车占比={DP45_SHARE:.2f}%  REAL_G={f2(REAL_G)}")
print("BUILD_OK")
