---
name: wallstreetcn-news
version: 1.0.0
description: 获取华尔街见闻财经新闻
author: wallstreetcn
source: https://skillhub.cn/skills/wallstreetcn-news
---

# 华尔街见闻新闻 Skill

获取华尔街见闻的财经新闻、头条、热文和搜索结果。

## API 接口

### 1. 获取最新文章
```
GET https://api-one-wscn.awtmt.com/apiv1/content/information-flow?channel=global&accept=article&limit=10
```

### 2. 获取头条文章
```
GET https://api-one-wscn.awtmt.com/apiv1/content/carousel/information-flow?channel=global&limit=10
```

### 3. 获取热门文章
```
GET https://api-one-wscn.awtmt.com/apiv1/content/articles/hot?period=all
```

### 4. 搜索文章
```
GET https://api-one-wscn.awtmt.com/apiv1/search/article?query={关键词}&limit=10
```

## 数据解析

### API 响应结构

**重要**：头条/carousel API 的文章字段嵌套在 `item → resource` 下，不是顶层。

```json
{
  "data": {
    "items": [
      {
        "resource_type": "article",
        "resource": {
          "title": "标题",
          "uri": "链接",
          "content_short": "摘要",
          "display_time": 0,
          "author": {
            "display_name": "作者名"
          }
        }
      }
    ]
  }
}
```

**常见坑**：
- `display_time` 是 Unix 时间戳（秒），不是字符串
- `content_short` 可能包含全角省略号 `…`，在 Python f-string 中需转义或避免直接嵌入

## 使用示例

### 获取最新新闻
```bash
curl "https://api-one-wscn.awtmt.com/apiv1/content/information-flow?channel=global&accept=article&limit=10"
```

### 搜索新闻
```bash
curl "https://api-one-wscn.awtmt.com/apiv1/search/article?query=中国石油&limit=10"
```

### 一键解析头条（推荐）
使用内置脚本直接获取格式化输出：
```bash
python3 ~/.hermes/skills/wallstreetcn-news/scripts/parse-headlines.py
```
支持 `--limit N` 参数控制条数，默认 10 条。

## 输出格式

```markdown
---
### 📰 华尔街见闻 · WALLSTREETCN
---

**1【文章标题】**
内容摘要（前 50 字左右）...
> [阅读全文](https://wallstreetcn.com/articles/...) · 作者：作者名 · 2026-03-27 11:00

---

> 💡 华尔街见闻 —— 帮助投资者理解世界
```

## Fallback Strategies for Non-Financial / Geopolitical News

When the 华尔街见闻 API returns **0 results** (common for geopolitical events like "UAE退出OPEC" or non-market topics), use this **multi-source fallback chain** discovered through trial and error:

### Source Reliability Ranking

| Priority | Source | URL Pattern | Status | Notes |
|:---:|:---|:---|:---:|:---|
| 1 | **澎湃新闻 (The Paper)** | `https://www.thepaper.cn/searchResult?searchWord={keyword}` | ✅ Reliable | Best for int'l news; has 新华社 content |
| 2 | **新浪财经** | `https://finance.sina.com.cn/` | ⚠️ Mixed | Good for finance-related geopolitics |
| 3 | **网易新闻** | `https://news.163.com/` | ❌ Often 404 | Avoid |
| 4 | **百度搜索** | `https://www.baidu.com/s?wd={keyword}` | ❌ CAPTCHA | Triggers verification; avoid in automation |
| 5 | **今日头条API** | `https://www.toutiao.com/api/search/content/...` | ❌ Reject | Returns `shark_decision: reject` |

### Recommended Fallback Workflow

```python
# Step 1: Try 华尔街见闻 API first
# If returns {"count":0,"items":null} → proceed to fallback

# Step 2: Navigate to 澎湃新闻 search
browser_navigate("https://www.thepaper.cn/searchResult?searchWord=阿联酋")

# Step 3: Identify relevant article in search results
# Look for links like /newsDetail_forward_{id}

# Step 4: Click article
browser_click("@newsDetail_forward_33077085")

# Step 5: Extract full article content
browser_snapshot(full=true)
# Content is in <main> → <paragraph> elements
```

### Real-World Example: UAE退出OPEC (2026-04-28)

**Trial-and-error log:**
- ❌ 华尔街见闻 API: `{"count":0,"items":null}` — API has no geopolitical coverage
- ❌ 今日头条 API: `shark_decision: reject` — blocked
- ❌ 百度搜索: CAPTCHA triggered immediately
- ❌ 网易新闻: 404 page
- ✅ **澎湃新闻**: Found 新华社 + 深度分析 articles within seconds

**Final sources used:**
1. `https://www.thepaper.cn/newsDetail_forward_33073123` — 新华社官方报道
2. `https://www.thepaper.cn/newsDetail_forward_33077085` — 澎湃新闻深度分析

### Forex / International Currency Intervention News (2026-05-05 Discovery)

**WallStreetCN API gaps are broader than geopolitics**: Topics like "日元干预 USD/JPY 160" also return `{"count":0,"items":null}`.

**Recommended approach for forex intervention events:**

```
Step 1: Bing search with ENGLISH queries (better for international events)
  → browser_navigate("https://www.bing.com/search?q=Japan+MoF+intervention+April+2026+yen")

Step 2: Read Bing featured snippets directly (often contains key facts)
  → Look for text blocks with numbers like "$32B" or "5 trillion yen"

Step 3: Try accessible smaller sites when major ones are blocked
  ✅ academicjobs.com — no paywall, no Cloudflare
  ✅ kantenna.com — accessible, quick load
  ❌ Reuters — bot detection
  ❌ SeekingAlpha — bot detection
  ❌ BabyPips — Cloudflare challenge
  ❌ TradingView — times out
  ❌ MarketPulse — Cloudflare challenge
```

**Real-World Example: Japan Yen Intervention April 30, 2026**

**Trial-and-error log:**
- ❌ 华尔街见闻 API: `{"count":0,"items":null}` — no forex intervention coverage
- ❌ 澎湃新闻 search: 0 results for "美元兑日元 160 干预"
- ❌ 中文 Bing queries: poor results for international forex events
- ❌ Reuters / SeekingAlpha / BabyPips / MarketPulse / TradingView: all blocked by bot detection
- ✅ **English Bing search**: Featured snippet revealed "5 trillion yen ($32B)" directly
- ✅ **academicjobs.com**: Full detailed article accessible without blocks

### Pitfalls Discovered

1. **百度 is unreliable**: Always triggers CAPTCHA in headless browser mode
2. **Toutiao API blocks programmatic access**: Returns empty `shark_decision: reject`
3. **News site structure varies**: 澎湃新闻 uses `newsDetail_forward_{id}` URLs; article body is in plain `<paragraph>` tags without heavy JS obfuscation
4. **Full snapshot needed**: Use `browser_snapshot(full=true)` to capture complete article text; compact mode misses content
5. **Major financial sites block aggressively**: Reuters, SeekingAlpha, BabyPips, MarketPulse, TradingView all have Cloudflare/bot detection
6. **English Bing queries outperform Chinese for international events**: Forex intervention, central bank actions, etc.
7. **Bing featured snippets are gold**: Often contain key numbers and facts without needing to click through

## 注意事项

1. API为公开接口，无需认证
2. 请遵守相关使用条款和版权规定
3. 建议缓存结果避免频繁请求
4. **For geopolitical / non-financial / forex topics**: Always prepare fallback to browser-based sources; financial news APIs often have gaps
5. **When researching international financial events**, start with English Bing search + featured snippet extraction before attempting blocked major sites
