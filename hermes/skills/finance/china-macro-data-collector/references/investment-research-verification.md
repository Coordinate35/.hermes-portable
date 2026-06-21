---
name: investment-research-verification
description: >
  Systematic approach for verifying investment claims when primary sources 
  (annual reports, SEC filings) are partially or fully inaccessible. 
  Emphasizes epistemic humility, user empowerment, and clear distinction 
  between verified facts and informed assumptions.
author: Assistant
created: 2026-04-20
tags: [finance, investment, research, verification, annual-reports, primary-sources]
---

# Investment Research Verification Workflow

## When to Use

- Making investment claims about a company's business structure, revenue sources, or market exposure
- User challenges your analysis and requests verification from primary sources
- You cannot fully access primary source documents (PDFs, annual reports, SEC filings)
- You need to distinguish between verified facts and industry conventions/assumptions

## Why This Matters

Investment decisions based on unverified assumptions can lead to significant losses. 
When you cannot access primary sources, being transparent about uncertainty is more 
valuable than feigning confidence.

## Core Workflow

### Step 1: Initial Assessment (Internal)

**Acknowledge what you know:**
- Industry conventions and historical patterns
- General business model characteristics
- Publicly available high-level information

**Identify what you DON'T know:**
- Specific current data points (e.g., exact sales distribution percentages)
- Recent changes in business structure
- Company-specific contractual arrangements

**Rate your confidence:**
- **High**: Based on verified data or extremely stable industry patterns
- **Medium**: Based on informed assumptions with some supporting evidence
- **Low**: Based on general industry knowledge without company-specific confirmation

### Step 2: Attempt Primary Source Verification

**Identify relevant documents:**
- Annual reports (Form 10-K, 20-F, 年报)
- Quarterly reports (Form 10-Q, 6-K, 季报)
- Investor presentations
- SEC filings/Exchange announcements

**Locate key data points:**
- Revenue breakdown by region/customer
- Sales distribution (domestic vs. international)
- Customer concentration
- Business segment performance

**Try to access documents:**
- Company IR website
- SEC EDGAR database
- Exchange disclosure platforms
- Direct document links

### Step 3: If Primary Sources Are Inaccessible

**CRITICAL PRINCIPLE: Do NOT pretend you have the data**

**Explicitly state your limitation:**
```
"I searched for [document name] at [URL], but cannot directly access 
the PDF content to extract the specific data on [data point]."
```

**Explain what you tried and why it failed:**
- "PDF cannot be parsed by browser tools"
- "Document requires authentication"
- "Website structure prevents automated access"
- "File format is not machine-readable"

**Acknowledge the impact on your analysis:**
```
"My previous assertion about [topic] is based on historical patterns, 
but I cannot confirm if it still holds for [current year]."
```

### Step 4: Provide Alternative Verification Paths

**Give the user specific, actionable steps:**

**For Annual Reports:**
1. Visit [specific URL - e.g., company IR page]
2. Navigate to "Investor Relations" → "Annual Reports" (or equivalent)
3. Download the [year] Annual Report (PDF)
4. Search for keywords: "revenue by region", "sales distribution", "geographic breakdown", "customer concentration"
5. Look for tables showing: Domestic vs. International revenue, sales by region, major customers

**For Investor Presentations:**
1. Check "Investor Relations" → "Presentations" or "Events"
2. Look for recent earnings call presentations
3. Often contains summary slides with key metrics

**For Direct Inquiry:**
- Provide IR contact information:
  - Phone: [IR phone number]
  - Email: [IR email address]
- Suggest specific questions:
  - "What is the current split between domestic and international sales?"
  - "Has there been any significant change in sales distribution in recent years?"
  - "What percentage of revenue comes from [specific region/customer type]?"

### Step 5: Recalibrate Your Analysis

**After admitting uncertainty:**

**Clarify what is based on solid data vs. assumptions:**
```
**High confidence:**
- [Solid facts you can verify]

**Medium confidence:**
- [Informed assumptions with some supporting evidence]

**Low confidence/Unknown:**
- [What you couldn't verify - the gaps in your knowledge]
```

**Update confidence levels:**
- Be explicit about which parts of your analysis need verification
- Acknowledge that your conclusions are conditional on unverified assumptions

**Offer conditional advice:**
```
"IF [assumption] is true, THEN [implication for investment strategy].
However, if [assumption] is false, the strategy would need to be revised."
```

## Response Template

```
Based on industry conventions, my analysis assumes [X]. However, I need to verify this against [Company]'s latest annual report.

**Attempted Verification:**
I searched for [document name] at [URL], but cannot directly access the PDF content to extract the specific data on [data point].

**What This Means:**
My previous assertion about [topic] is based on historical patterns, but I cannot confirm if it still holds for [current year].

**How You Can Verify:**
1. Visit [specific URL]
2. Download [document name]
3. Look for [specific section/table]
4. Check if [data point] has changed

**Updated Assessment:**
- High confidence: [solid facts]
- Medium confidence: [informed assumptions]  
- Low confidence/Unknown: [what couldn't be verified]
```

## Key Principles

1. **Epistemic Humility**: Better to admit what you don't know than to confidently assert unverified claims
2. **User Empowerment**: Give users tools to verify themselves, rather than leaving them dependent on your (incomplete) analysis
3. **Distinguish Assumptions from Facts**: Clearly label which parts of your analysis are based on general knowledge vs. specific verified data
4. **Transparency about Limitations**: Explain what you tried and why it failed
5. **Conditional Advice**: Frame recommendations based on the condition that assumptions hold true

## Foreign Government Primary Source Verification

When verifying claims about foreign macroeconomic or policy events (e.g., central bank interventions, fiscal data, regulatory changes):

### Step 1: Identify the Official Data Publisher

| Country/Region | Typical Publisher | Data Format |
|:---|:---|:---|
| Japan (FX intervention) | Ministry of Finance (MOF) | CSV at `mof.go.jp/.../feio/` |
| US (SEC filings) | SEC EDGAR | HTML/TXT/XBRL |
| China (macro data) | NBS / PBOC | HTML/Excel |
| EU (fiscal) | ECB / Eurostat | SDMX/CSV/XLS |

### Step 2: Handle Encoding Issues

East Asian government sites frequently use non-UTF-8 encodings:

```python
# Japanese government CSVs often use cp932 (Shift-JIS)
encodings_to_try = ['utf-8', 'cp932', 'euc-jp', 'shift_jis']
for enc in encodings_to_try:
    try:
        data = raw_bytes.decode(enc)
        break
    except UnicodeDecodeError:
        continue
```

**Common encoding patterns:**
- **Japan**: cp932 / Shift-JIS (not UTF-8)
- **China**: GB2312 / GBK (though UTF-8 is increasingly common)
- **Korea**: EUC-KR / CP949

### Step 3: Cross-Reference Claimed Numbers Against Historical Records

This is a powerful hallucination-detection technique:

1. Extract the **specific number** from the claim (e.g., "5.48 trillion yen")
2. Search the official dataset for that number or nearby values
3. Check if the number actually appears in a **different time period**
4. If a claimed "2026" figure matches a "2024" historical record exactly → **high probability of fabricated date**

**Example from practice:**
- Claim: "5.48 trillion yen intervention on April 30, 2026"
- Official data: No 2026 records; 2024 July-September quarter total = 5.5348 trillion
- Conclusion: The "5.48 trillion" figure does not exist in official records. It appears to be a slightly altered version of the 2024 Q3 total, with the date shifted forward by 2 years.

### Step 4: Verify Named Individuals

Government personnel lists are usually public:
- Cross-reference claimed officials against current government directories
- Common hallucination: assigning people to wrong ministries or wrong time periods
- Example: A claimed "Finance Minister Katayama" was actually a different minister in a different role; the real Finance Minister was Kato Katsunobu.

### Step 5: Network Access Strategy

Foreign official sites may have connectivity issues. Try in order:
1. `browser_navigate` to the main portal
2. `curl` with `-H "User-Agent: Mozilla/5.0"` for direct file access
3. `python urllib` with SSL context disabled if needed (`ctx.verify_mode = ssl.CERT_NONE`)
4. `r.jina.ai/http://...` as a text-extraction fallback (may fail for some sites)
5. Search for alternative mirrors or press release aggregators

## Common Pitfalls to Avoid

- ❌ Pretending you have data you can't access
- ❌ Making up specific numbers to sound authoritative  
- ❌ Dismissing user requests for verification as unnecessary
- ❌ Providing vague "just Google it" responses instead of specific guidance
- ❌ Continuing to act confident after admitting you don't have the data
- ❌ Accepting AI-generated reports at face value without primary source verification
- ❌ Assuming all government CSVs use UTF-8 encoding

## Good Practices

- ✅ Admitting "I tried X but couldn't access Y because Z"
- ✅ Providing step-by-step instructions for user verification
- ✅ Distinguishing between "I know this" and "I assume this based on historical patterns"
- ✅ Offering conditional advice based on the status of assumptions
- ✅ Encouraging users to verify and report back

## Investment Strategy Transition Analysis

When a user corrects your understanding of a dynamic investment strategy (e.g., "the recommendation is no longer X, it is now Y"), follow this systematic transition analysis workflow:

### Step 1: Halt and Verify the Premise

**Do NOT continue analyzing with the old assumption.**

1. **Acknowledge the correction explicitly**
   ```
   "Thank you for the correction. My previous analysis assumed [old strategy]. 
   I need to verify the factual basis of [new strategy] before proceeding."
   ```

2. **Confirm the key factual premises** with the user:
   - **Timing**: When was the transition announced/observed?
   - **Definition**: What exactly does the new strategy entail? (e.g., "oil" = broad energy assets, not just crude)
   - **Drivers**: What are the stated core drivers? (e.g., dollar depreciation + energy value regression)
   - **Nature**: Is this a tactical rotation or a structural shift?

3. **Check your memory stores** (`session_search`, `fact_store`) for any prior records
   - If found: verify against user's claim; update if outdated
   - If not found: admit the gap and rely on user-provided facts

### Step 2: Backtrack the Old Strategy's Derivation

Before analyzing the new strategy, understand **why the old one made sense** and **what changed**:

| Question | Why It Matters |
|----------|---------------|
| What macro conditions made the old strategy valid? | Establishes the baseline |
| What was the core derivation chain? | Reveals the logical foundation |
| What specific trigger invalidated it? | Identifies the reversal signal |

**Example from practice:**
- Old: "短股长金" rested on **severe real negative interest rates** (>5%) + **stagflation** quadrant
- Trigger for shift: **International monetary factors** (dollar depreciation) overwhelmed **domestic macro factors**, making energy a higher-beta play than gold

### Step 3: Validate the New Strategy with Real Data

**Use quantitative data to verify the new strategy's premises**, not just qualitative reasoning:

```
1. Collect macro data (CPI, M2, GDP, LPR, housing, etc.)
2. Re-calculate the framework indicators (real inflation, real interest rate, four-quadrant position)
3. Collect global market data (gold, oil, DXY, US debt, etc.)
4. Cross-check: Do the data support the stated drivers?
5. Identify contradictions: Is domestic data aligned with the strategy, or is the strategy driven by external factors?
```

**Critical insight from practice:**
If domestic four-quadrant analysis suggests "stocks" but the strategist recommends "energy," this means **international monetary factors have overwhelmed domestic macro factors**. Explicitly state this divergence.

### Step 4: Build the Exit Signal Framework

A strategy without an exit condition is just a hope. For the new strategy, define:

| Signal Category | Specific Indicators | Thresholds | Frequency |
|-----------------|-------------------|------------|-----------|
| **Core driver reversal** | Dollar trend (DXY) | Break 105 (up) or 90 (down) | Weekly |
| **Valuation exhaustion** | Sector P/E, P/B | >80th percentile historically | Monthly |
| **Framework quadrant shift** | Real inflation, GDP | Cross 5% thresholds | Monthly |
| **Black swan** | Liquidity crisis markers | Yen >150, bond auction failure | Daily during stress |

**Document the baseline**: Record the current values at strategy initiation so future shifts can be measured.

### Step 5: Scenario-Based Next-Phase Prediction

Instead of predicting a single outcome, construct **probability-weighted scenarios**:

| Scenario | Probability | Trigger | Next Phase |
|----------|------------|---------|-----------|
| **Base case** | ~60% | Gradual driver exhaustion | Smooth transition to next asset class |
| **Crisis case** | ~25% | Liquidity shock (e.g., Japan implosion) | Forced exit to safe haven |
| **Extreme case** | ~15% | Currency/credit collapse | Flight to real assets |

**Conditional recommendations**: Always frame advice as "IF [scenario] THEN [action]."

### Common Pitfalls in Strategy Transition Analysis

- ❌ **Continuing with outdated assumptions** after being corrected
- ❌ **Guessing the strategist's reasoning** instead of verifying with data
- ❌ **Ignoring domestic vs. external factor divergence**
- ❌ **Failing to define exit conditions** when validating a new strategy
- ❌ **Presenting single-point forecasts** instead of scenario ranges
- ❌ **Over-relying on memory** when the user explicitly states a change

## Integration with Investment Analysis

This workflow is particularly important for:
- Revenue/earnings quality assessment
- Geographic/customer concentration analysis
- Regulatory/政策 impact evaluation
- Business model verification
- Competitor comparison validation

**Related Concepts from Investment Framework:**
- "右派投资法" (Right-foot/Right-shoulder theory) - Wait for confirmation before acting
- "实质负利率分析" - Verify data before calculating
- "政策驱动投资" - Verify policy implementation, not just announcements

## Data Source Obsolescence Patterns

Official government data URLs can silently stop updating while remaining accessible:

| Data | Old URL (STALE) | New URL (CURRENT) | Last Updated |
|:---|:---|:---|:---|
| US TIC foreign holders | `ticdata.treasury.gov/Publish/mfh.txt` | `ticdata.treasury.gov/.../slt_table5.txt` | mfh.txt stuck at 2023-01 |
| US TIC foreign holders (HTML) | — | `.../slt_table5.html` | Check `<td>2026-03</td>` |

**Detection pattern:** If data appears current (site responds) but the latest date in the file is >1 year old, search for an alternative file in the same directory tree. Government sites often create new files rather than updating old ones when formats change.

Also note: mfh.txt was fixed-width format; slt_table5.txt is **tab-separated (TSV)**. Same data, different parsing.

## Final Note

This skill is about **intellectual honesty in investment research**. The goal is not to have all the answers, but to:
1. Clearly distinguish what you know from what you assume
2. Give users the tools to verify what matters to their investment decision
3. Avoid overconfidence that leads to poor investment outcomes

**Remember**: In investing, "I don't know" is often more valuable than a confident wrong answer.