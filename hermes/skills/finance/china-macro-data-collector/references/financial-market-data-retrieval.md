---
name: financial-market-data-retrieval
description: Retrieve real-time stock quotes, market indices, and commodity prices from Chinese financial websites and provide investment analysis
tags: [finance, stocks, market-data, investment, hong-kong-stocks, a-shares, real-time-quotes]
---

# Financial Market Data Retrieval & Analysis

## When to Use
- User asks about specific stock prices (港股, A股, 美股)
- User asks about market indices (上证指数, 恒生指数, etc.)
- User asks about commodity prices (原油, 黄金, etc.)
- User wants investment analysis based on current market data

## Tools Required
- browser_navigate
- browser_snapshot
- browser_scroll (optional)

## Data Sources

### 1. East Money (东方财富) - Primary Source
**URL Pattern:** `https://quote.eastmoney.com/hk/{stock_code}.html` (for HK stocks)
**URL Pattern:** `https://quote.eastmoney.com/{market}{code}.html` (for A-shares)

**Examples:**
- 中海油 (0883.HK): `https://quote.eastmoney.com/hk/00883.html`
- 贵州茅台 (600519.SH): `https://quote.eastmoney.com/sh600519.html`
- 宁德时代 (300750.SZ): `https://quote.eastmoney.com/sz300750.html`

**Market Indices Page:**
- `https://quote.eastmoney.com/center/gridlist.html#hs_a_board` (A-share market overview)

### 2. Sina Finance (新浪财经) - Alternative Source
**URL Pattern:** `https://stock.finance.sina.com.cn/hkstock/quotes/{code}.html` (for HK stocks)
**URL Pattern:** `https://finance.sina.com.cn/realstock/company/{market}{code}/nc.shtml` (for A-shares)

**Examples:**
- 中海油: `https://stock.finance.sina.com.cn/hkstock/quotes/00883.html`

## Data Extraction Guide

### Key Data Points to Extract:
1. **Current Price** (最新价)
2. **Price Change** (涨跌额)
3. **Percentage Change** (涨跌幅)
4. **Open Price** (今开盘)
5. **Previous Close** (昨收盘)
6. **High Price** (最高价)
7. **Low Price** (最低价)
8. **Volume** (成交量) - if available
9. **Amplitude** (振幅) - if available

### Market Indices to Track:
- 上证指数 (Shanghai Composite)
- 深证成指 (Shenzhen Component)
- 恒生指数 (Hang Seng Index)
- 道琼斯 (Dow Jones)
- 纳斯达克 (Nasdaq)

### Commodities to Track:
- NYMEX原油 (Crude Oil)
- COMEX黄金 (Gold)
- COMEX白银 (Silver)
- LME铜 (Copper)

## Analysis Framework

After retrieving data, provide analysis based on:

### 1. Technical Analysis
- Current price position (near support/resistance)
- Trend direction (based on price action)
- Key levels (highs, lows, support, resistance)

### 2. Market Context
- Overall market sentiment (bullish/bearish)
- Sector performance (for stock-specific analysis)
- Global market correlation

### 3. Risk Assessment
- Volatility (amplitude)
- Key risk events (earnings, policy changes)
- Stop-loss levels

### 4. Investment Recommendation
- Suitability for different investor types
- Entry/exit strategies
- Position sizing

## Example Workflow

### Scenario: User asks about 中海油 (CNOOC)

```
1. Navigate to: https://quote.eastmoney.com/hk/00883.html
   OR: https://stock.finance.sina.com.cn/hkstock/quotes/00883.html

2. Extract key data:
   - Current Price: 26.98 HKD
   - Change: +0.28 (+1.05%)
   - Open: 26.70
   - High: 27.08
   - Low: 26.38
   - Prev Close: 26.70

3. Get market context:
   - 上证指数: 4051.43 (-0.10%)
   - 恒生指数: 26160.33 (-0.89%)
   - NYMEX原油: 85.17 (-10.05%) ⚠️

4. Provide analysis:
   - Stock is up today but oil crashed 10%
   - CNOOC is pure upstream oil play
   - High risk due to oil price crash
   - Recommend: Wait for stabilization
```

## Pitfalls to Avoid

1. **Don't rely on a single source** - Always cross-check with multiple sites if data seems inconsistent
2. **Be aware of market hours** - Data may be stale if markets are closed
3. **Watch for currency differences** - HK stocks in HKD, A-shares in CNY
4. **Distinguish real-time vs delayed** - Some free sources have 15-minute delays
5. **Check market status** - Chinese markets have different trading hours and holidays

## Related Skills

- investment-analysis-framework - For comprehensive investment analysis
- technical-analysis - For chart pattern and indicator analysis
- financial-statement-analysis - For fundamental analysis