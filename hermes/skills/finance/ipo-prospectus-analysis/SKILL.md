---
name: ipo-prospectus-analysis
description: Use when 找/下载/翻译/分析 IPO 招股书（S-1 等）。
category: finance
version: 1.0.0
author: coordinate35
license: proprietary
metadata:
  hermes:
    tags: [ipo, sec, edgar, prospectus, translation]
    related_skills: [article-archive, pdf-generation-reportlab]
---

# IPO 招股书：定位、下载、翻译、分析

覆盖“找一家公司的招股书”“把招股书翻成中文”“分析募资用途/风险因素/财务”这类任务。**第一原则：一切以 SEC（或对应交易所）原文为准，不用新闻稿或传闻补数字。**

## When to Use（触发条件）

- “找/下载 XX 的招股书 / S-1 / 红鲱鱼 / 招股说明书 / IPO 文件”
- “把招股书翻译成中文 / 翻译这份年报”
- “分析 XX 招股书里的财务 / 募资用途 / 风险因素 / 控制权结构”
- 用户贴出 S-1 链接、EDGAR URL、或“XX 要上市了，帮我看看文件”

## 第 1 步：确认文件是否真的存在

公司可能只是**保密递交**（confidential draft S-1），公开文件尚不存在。先查再答，别假设“要上市=有 S-1”。

- 提交历史 JSON：`https://data.sec.gov/submissions/CIK##########.json`（CIK 补足 10 位）
- 归档目录：`https://www.sec.gov/Archives/edgar/data/<CIK>/<accession去掉横线>/index.json`
- 公司 IR 页 / SEC 全文检索 `https://efts.sec.gov/LATEST/search-index?q=...`
- 港股：HKEXnews；A 股：巨潮资讯网（cninfo）

`curl` 必须带 UA，否则被 403：

```bash
curl -s -A "Mozilla/5.0 (research; contact@example.com)" -o /tmp/index.json \
  "https://www.sec.gov/Archives/edgar/data/<CIK>/<accession>/index.json"
```

若只有保密递交：如实说明“公开招股书尚未提交”、给出保密递交日期与公开文件预期窗口，**不要用媒体拆解稿冒充招股书**。

## 第 2 步：下载原始文件

`index.json` 的 `directory.item[]` 里：

- 主文档 = 最大的 `.htm`（如 `anthropicpbc-sx1.htm`，十几 MB）
- 其余是 exhibit（承销协议、章程、审计同意书等），需要时单独下
- 同时存 `index.json` 与 `submissions.json` 作元数据（filingDate / form / accessionNumber）

```bash
mkdir -p ~/hermes_data/ipo/<公司>
curl -s -A "Mozilla/5.0 (research; contact@example.com)" \
  -o ~/hermes_data/ipo/<公司>/<doc>.htm \
  "https://www.sec.gov/Archives/edgar/data/<CIK>/<accession>/<doc>.htm"
```

校验：文件字节数与 `index.json` 的 `size` 一致；HTML 首行应含 `As filed with the Securities and Exchange Commission on <日期>`。

## 第 3 步：渲染成可读 PDF

Chrome 无头打印即可，不需要装 pandoc/weasyprint：

```bash
/usr/bin/google-chrome --headless=new --disable-gpu --no-sandbox \
  --virtual-time-budget=120000 --no-pdf-header-footer \
  --print-to-pdf=<out.pdf> file://<绝对路径>/<doc>.htm
```

校验：`pdfinfo` 看页数；`pdftoppm -f 1 -l 1 -r 80 -png` + `vision_analyze` 抽 1–2 页看封面与表格。

**坑：Chrome 会重新分页。** PDF 物理页 ≠ 原件页脚编号，且前后偏移不一致（早期页和后期页相差几十页）。**不要用“原件页码 + 固定偏移”定位章节**，永远按章节名/内容定位。

## 第 4 步：提取文本（检索与翻译的基础）

```bash
pdftotext -layout <out.pdf> <out.txt>
```

**坑：SEC 的 HTML 文本层是硬换行 + 绝对定位叠加。** 直接按行 `grep/search_files` 搜整句几乎必然 0 命中。正确做法是归一化后搜：

```python
import re
t = open(txt, encoding='utf-8').read()
n = re.sub(r'\s+', ' ', t)          # 硬换行全部压平
hits = [m.start() for m in re.finditer(re.escape('Summary Consolidated Financial Data'), n, re.I)]
```

定位章节的可靠顺序：① 读 TOC 拿**原件页码**（只用于知道章节顺序）；② 在归一化文本里按章节标题/首句定位字符偏移；③ 需要页面级文本时用 `pdftotext -f N -l N` 逐页扫内容匹配（不是靠页码换算）。

## 第 5 步：分叉——分析 或 翻译

### 5a 财务拆解（分析类）

先读 `Summary Consolidated Financial and Other Data`：收入、费用分项（算力/人员/销售/其他）、经营亏损、其他收支、净亏损、每股亏损。必查四件事：

1. **净亏损里有多少是非现金公允价值变动**（可转债/衍生负债/SAFE）。把会计噪音当经营恶化是最常见的误读。
2. **收入构成**：按量计费 vs 订阅、各自占比与增速。
3. **单位经济**：NRR、客户分层（≥$10 万/≥$100 万/≥$1000 万）、人均 TTM 收入、算力费用增速 vs 收入增速。
4. **募资去向**：公司所得 vs 售股股东减持所得要分开；初步招股书的价格、股数、净额通常留白。

同时看 `Risk Factors Summary`（摘要里的十几条）与 `Capitalization` / `Our Capital Structure`（多类股与投票权）。

### 5b 中文精译（本用户默认口径）

**先确认范围再动手**。全文 300+ 页、数十万词，全译要数小时且成本高；默认交付是**核心章节精译 PDF，约 15–25 页 A4**。给用户三四个选项：核心章节 / 全文分批 / 中英对照 / 指定章节。

章节范围（按此顺序）：发行概要 → 招股说明书摘要 → 摘要财务数据（完整表格）→ 风险因素摘要（逐条）→ 募资用途 → 资本化（含股本表）→ MD&A → 业务 → 承销 → 附录（原文页码索引、术语表、关键数字）。

**铁律：原文留白的字段一律标 `【原文留白】`。** 初步招股书的价格区间、发行股数、净募资额、算力承诺金额、最近一季收入、RSU 预扣税等常为空白——绝不估算、绝不用新闻里的数字填。只翻你实际读到的段落，没读的章节不要“按常识”补写。

译稿末尾加「阅读提示」（把两个亏损口径分开、控制权集中、募资主要不流向公司等），并注明“仅供研究参考”。

## 第 6 步：生成中文 PDF（表格必须能排）

用本技能自带脚本 `scripts/build_cn_pdf.py`（支持 `#` / `##` / `###`、`-` 列表、`|` 管道表格、自动页脚页码、数字列右对齐）：

```bash
PYTHONPATH= ~/hermes_data/rl-venv/bin/python \
  ~/.hermes/skills/finance/ipo-prospectus-analysis/scripts/build_cn_pdf.py <稿.md>
```

- **必须带 `PYTHONPATH= ` 前缀**：Hermes 注入的 3.14 包路径会污染 rl-venv 的 reportlab/PIL。
- **坑：reportlab 数字列太窄会把长数字折行**（`1,821,084,860` 断成两行）。修法：数字单元格 `wordWrap='LTR'`；超长股数干脆移出表格，用表下注释行列出。
- 校验：`pdfinfo` 页数 → `pdftotext -f N -l N -layout` 看数字是否串列 → `pdftoppm` + `vision_analyze` 看表头/对齐。

## 交付

- 文件统一放 `~/hermes_data/ipo/<公司>/`，附 `README.md`（来源 URL、accession、CIK、提交日期、各文件说明、sha256）。
- QQ 发 PDF 用 `MEDIA:<绝对路径>`，并在文字里说明：页数、覆盖章节、留白字段、未译部分。
- 引用页码时写**章节名**，不要写 Chrome PDF 的物理页码。

## 反模式

- ❌ 用新闻稿/爆料代替原文：媒体常把“净亏损”写成经营亏损，也会引用文件里留白的数字。
- ❌ 把 `net loss` 当经营亏损：先扣掉公允价值变动再看经营。
- ❌ 拿 Chrome PDF 的页数去引用“第 124 页”。
- ❌ 全译不确认范围就开工：先给选项，用户选定再动。
- ❌ 留白字段自行估算填数（价格、股数、募资额、承诺金额）。
