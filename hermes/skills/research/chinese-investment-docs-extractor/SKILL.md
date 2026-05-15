---
name: chinese-investment-docs-extractor
description: Systematically extract investment analysis frameworks from Chinese finance/investment PDF documents
triggers:
  - extract investment framework from PDF
  - analyze Chinese investment documents
  - 提取投资框架
  - 分析投资文档
  - process finance PDFs
  - extract 四矩阵
  - extract cycle theory
  - 周期理论提取
requirements:
  - User has PDF documents at /home/coordinate35/virtualbox_share/luqiyuan/docs or similar path
  - Documents are in Chinese
  - Content relates to investment/finance frameworks
---

# Chinese Investment Document Framework Extractor

## Overview

This skill extracts structured investment analysis frameworks from Chinese finance/investment PDF documents. It uses a systematic approach to identify key concepts, frameworks, and decision-making methodologies.

## Prerequisites

- PDF files located at user-specified path (typically `/home/coordinate35/virtualbox_share/luqiyuan/docs/`)
- System has `pdftotext` available (preferred over PyMuPDF - user denied installation)

## Pre-Extraction: Document Access

If the user references a Chinese government policy document or whitepaper (白皮书) but does not have the PDF yet, consult `references/chinese-policy-document-access.md` for layered strategies to locate it. Key points:

- Direct access to `scio.gov.cn` usually fails (JS cookie challenges, anti-bot)
- E-commerce book search (当当, 京东) reveals ISBN, publisher, publication date reliably
- Sogou WeChat search finds public-account summaries with full text
- English versions may exist on `english.www.gov.cn/archive/whitepaper/`

## Extraction Process

### Phase 1: Initial Extraction

1. **List PDF files** in target directory:
   ```bash
   ls -la /path/to/docs/*.pdf
   ```

2. **Extract all PDFs to text** using pdftotext:
   ```bash
   pdftotext /path/to/docs/file.pdf /tmp/extracts/file.txt
   ```

3. **Initial keyword scan** for core frameworks:
   - 四矩阵 / 资产矩阵 / 矩阵
   - 短股长金
   - 右派投资法 / 右脚右肩
   - 三三四原则
   - MACD / 一板斧
   - 周期理论: 朱格拉, 基钦, 季耶夫, 康波
   - 三流理论 / 资本流转
   - 货币三层次
   - 实质负利率
   - 中庸投资

### Phase 2: Deep Framework Extraction

For each identified framework, extract detailed content:

#### 四矩阵 (Four Matrix) Framework
Search for:
- 四矩阵定义 and asset classifications (现金/动产/不动产/商品)
- 四种形态: 高高, 高低, 低低, 低高
- Each形态's characteristics and investment strategies
- 实质负利率判断标准
- Historical examples (e.g., 2008-2018 中国高高形态)

#### Cycle Theory
Search for:
- 朱格拉周期: 上升期/爆发期/清算期 (each ~3-4 years)
- 基钦周期: ~40 months
- 季耶夫/康波周期: 60-year technology cycles
- Current cycle positions (e.g., 中国 vs 美国周期错位)

#### Investment Strategies
Search for:
- 短股长金 logic and implementation
- 右派投资法 (右脚买入/右肩卖出)
- 三三四原则 allocation
- MACD technical indicators

### Phase 3: Structured Compilation

Organize extracted content into:

```
### Core Theoretical Frameworks
- Capital flow theory (三流理论)
- Currency hierarchy theory (货币三层次)
- Cycle theories (detailed with phases)

### Investment Strategies
- Strategy name and definition
- Implementation rules
- Historical examples

### Analytical Frameworks
- 四矩阵 with four形态
- Decision criteria for each形态
- Capital flow logic

### Practical Operation Points
- Entry/exit rules
- Position management
- Risk control

### Investment Philosophy
- Mental cultivation principles
- Core maxims/quotes section
```

### Phase 4: Verification

If user indicates content is missing:

1. **Identify missing keywords** from user feedback
2. **Deep search** in extracted text files:
   ```python
   for line in lines:
       if keyword in line:
           extract context (±5 lines)
   ```
3. **Cross-reference** multiple PDF files for consistent frameworks
4. **Update memory** with complete framework

## Key Chinese Terms to Search

| Concept | Search Terms |
|---------|-------------|
| Four Matrix | 四矩阵, 资产矩阵, 高高, 高低, 低低, 低高 |
| Cycles | 朱格拉, 基钦, 季耶夫, 康波, 周期判断 |
| Interest Rates | 实质负利率, 名义利率, 通胀 |
| Strategies | 短股长金, 右派投资, 右脚, 右肩, 三三四 |
| Technical | MACD, 一板斧, 金叉, 死叉 |
| Philosophy | 中庸, 允执厥中, 正心以中 |

## Common Pitfalls

1. **Don't miss 四矩阵** - this is a core framework often initially overlooked
2. **Don't miss cycle phases** - 朱格拉周期 has three distinct phases (上升期/爆发期/清算期)
3. **Check all PDF files** - frameworks may be distributed across multiple years (2019/2020/2021/补讲)
4. **Extract context** - always get ±3-5 lines around keyword matches for complete meaning
5. **Verify completeness** - ask user to confirm if any key frameworks are missing

### Phase 3: Structured Compilation

Organize extracted frameworks for memory storage with:
- Clear hierarchical headings
- Bullet points for specific rules/criteria
- Historical examples where available
- Investment maxims/quotes section
- Character count awareness (memory limit ~2200 chars)

#### Specific Formulas to Extract

**Real Inflation Calculation (还原后实质通胀率):**

1. **Core Formulas:**
   - `实质利率 = 名义利率 + 实质通胀`
   - `实质负利率 = 实质通胀率 - 名义利率`
   - Alternative: `实质负利率 = 实质通胀率 + 名义利率` (check context for correct sign)

2. **Numerical Example (from 2021 lecture):**
   - 名义利率 = 2.5%
   - 实质通胀 = 8%
   - 实质利率 = 2.5% + 8% = 10.5%

3. **Key Distinction:**
   - Official CPI (统计局公布) ≠ Real inflation
   - Real inflation requires "restoration" (还原) calculation
   - Real inflation typically 5-15% (China 2008-2018) vs official figures much lower

4. **Four-Quadrant Decision Matrix dependency:**
   - 高高 (High growth + High inflation): Real negative rate 10-15% → Real estate
   - 低低 (Low growth + Low inflation): Lower real negative rate → Cash/bonds
   - 高低 (High growth + Low inflation): Low/positive real rate → Real economy/stocks
   - 低高 (Low growth + High inflation): Very high real negative rate → Gold

5. **Historical Reference Data (China 2008-2018):**
   - Real inflation: never below 5%, peak 10-15%
   - Nominal lending rate: 4-5%
   - Real negative interest rate range: 5-15%

6. **Key Quote (from 2021 lecture):**
   > "我说的通胀超过两位数不是统计局公布的CPI，是我们还原后的实质通胀"

**MV=PQ (Fisher Equation) Context:**
- Search for applications of `MV=PQ` in asset price analysis
- Look for explanations of how M2 expansion relates to inflation
- Extract discussions of velocity (V) changes and their impact

### Phase 5: Holographic Memory Import (fact_store)

For durable, queryable storage, use `fact_store` (not `memory`) to store extracted frameworks.

**Precondition check:**
1. Check if extracted text already exists:
   ```bash
   ls -la /home/coordinate35/hermes_data/pdf_extracts/
   ```
2. If already extracted, skip pdftotext and work directly from existing `.txt` files.

**Import workflow:**
1. **Batch keyword search** with `execute_code` Python script:
   ```python
   keywords = {
       "四矩阵": ["四矩阵", "高高", "低高"],
       "短股长金": ["短股长金"],
       ...
   }
   # Search across all .txt files, extract ±3 lines context
   ```
2. **Deep context extraction** for each core concept found:
   - Use `read_file` or `execute_code` to pull ±5 lines around matches
   - Cross-reference multiple PDFs for consistent definitions
3. **Structured import** via `fact_store action=add`:
   - `category`: "project"
   - `content`: One core concept per fact, concise but complete
   - `tags`: Comma-separated, include author name + domain + concept name
     - Example: `卢麒元,投资,四矩阵,资产配置,资本流动`
4. **Batch in groups of ≤5 facts** to avoid overwhelming context
5. **Verify completeness** by searching fact_store for known concepts:
   ```
   fact_store action=search query="四矩阵"
   ```

**Why fact_store over memory:**
- fact_store supports structured queries (`search`, `probe`, `reason`)
- Tags enable cross-referencing across sessions
- Trust scoring helps identify which facts are most reliable
- No 2200 char limit per entry

## Example Usage

User: "请提取这些PDF中的投资框架到记忆"
→ List PDFs → Check for existing extracts in pdf_extracts/ →
→ Search for key frameworks with execute_code → Extract context →
→ Import into fact_store with category=project and rich tags →
→ Ask user: "是否遗漏了任何重要框架如四矩阵或周期判断?"

User: "我记得有四矩阵内容"
→ Deep search for 四矩阵, 高高, 高低, 低低, 低高 in extracts →
→ Extract four形态 definitions and strategies →
→ Add/update fact_store entries → Verify with fact_store action=search