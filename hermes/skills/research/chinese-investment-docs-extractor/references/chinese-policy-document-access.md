# Chinese Policy Document / Whitepaper Access Strategies

## Problem

Chinese government whitepapers (白皮书) are published by the State Council Information Office (SCIO / 国务院新闻办). Direct access to `scio.gov.cn` frequently fails due to:

- **JS cookie challenges**: Returns obfuscated JavaScript that sets a cookie and redirects (HTTP 521, empty page with `<script>document.cookie=...`)
- **Anti-bot detection**: Aggressive bot detection blocks non-browser access
- **HTTP-only**: The site does not support HTTPS reliably
- **Link rot**: News agency mirrors (e.g. Xinhua) often 404 after a few months

## When this applies

- User shares a page/photo from a policy whitepaper and asks for the full text
- Need to verify a citation like `scio.gov.cn/zfbps/zfbps_2279/202504/t20250409_889794.html`
- Researching policy documents for investment/macro analysis (e.g. 中美经贸, 双碳, 贸易政策)

## Strategy: Layered Search

### Layer 1 — Direct access (rarely works from agent environment)

```bash
# Try direct fetch (usually blocked)
curl -s http://www.scio.gov.cn/zfbps/zfbps_2279/202504/t20250409_889794.html
# Returns: <script>document.cookie=... location.href=...</script>
```

**Status codes to recognize:**
- `521` — Web server is down (Cloudflare/anti-bot)
- Empty page with only `<script>` — JS cookie challenge
- `404` from news mirrors — Xinhua, People’s Daily links expire

**Anti-bot signature (scio.gov.cn specific):**
The site returns a short `<script>` block that sets `__jsl_clearance` via obfuscated string concatenation, then redirects to the same path. Example pattern:
```html
<script>document.cookie=('__jsl_clearance=')+...;location.href=location.pathname+location.search</script>
```
This is a **multi-layer challenge**: even libraries purpose-built for JS challenges (e.g. `cloudscraper`) return 521 here. Headless browser navigation also yields an empty page because the challenge executes but subsequent validation fails (the environment is fingerprinted).

> **Implication**: Do not spend more than one quick attempt on direct fetch/browser for scio.gov.cn. Immediately fall back to Layer 2 (e-commerce book search) or Layer 3 (WeChat mirrors).

### Layer 2 — E-commerce book search (highly reliable)

Chinese whitepapers are published as formal books with ISBNs. E-commerce sites index them immediately.

**Dangdang (当当):**
```bash
# Search by document title
curl -s "http://search.dangdang.com/?key=百分编码标题" \
  -H "User-Agent: Mozilla/5.0"
```

**What to extract:**
- **Publisher** (出版社): e.g. 人民出版社, 外文出版社
- **ISBN**: e.g. `978-7-01-027222-1`
- **Format**: 32开本, 16开本
- **Publication date**: e.g. 2025年4月
- **Foreign language editions**: e.g. 英文版, 德文版, 俄文版

**Example result from this session:**

| Field | Value |
|-------|-------|
| Title | 关于中美经贸关系若干问题的中方立场 |
| Publisher | 人民出版社 |
| Date | 2025年4月 |
| ISBN (32开) | 978-7-01-027222-1 |
| ISBN (16开) | 978-7-01-027223-8 |
| Languages | 中/英/法/德/俄/日/西班牙文 |

### Layer 3 — Sogou WeChat search

WeChat public accounts (公众号) often publish the full text or chapter-by-chapter breakdowns of whitepapers.

```bash
# Search Sogou WeChat
curl -s "https://weixin.sogou.com/weixin?type=2&query=白皮书标题" \
  -H "User-Agent: Mozilla/5.0"
```

**Note:** Sogou WeChat links require a redirect through `weixin.sogou.com/link?url=...` and may trigger CAPTCHA. Use browser tools if you need to read the actual article content.

### Layer 4 — English version via gov.cn

Some whitepapers have English translations published on `english.www.gov.cn/archive/whitepaper/`.

```bash
curl -s http://english.www.gov.cn/archive/whitepaper/ | grep -i "china-us\|trade\|economic"
```

**Note:** Not all whitepapers are translated. Check the publication list first.

### Layer 5 — Government portal search

```bash
# gov.cn policy library search API
curl -s "https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary&q=标题&page=1&pageSize=10"
```

**Limitation:** Only indexes policy documents, not all whitepapers. May return `{"code": 1001, "msg": "抱歉，没有找到相关结果"}`.

## What to report back

When full text is inaccessible, report:

1. **Document identity**: Title, author (e.g. 国务院新闻办公室), date
2. **Publication details**: Publisher, ISBN(s), format(s), language editions
3. **Access status**: Which layers succeeded/failed and why
4. **Alternative access**: Suggest the user open the scio.gov.cn link directly in their own browser, or purchase the book
5. **Content summary**: If you found a partial citation or page image, summarize the key argument

## Investment Analysis Hook

For policy whitepapers relevant to investment (e.g. 中美经贸, 贸易政策, 产业政策):

- Note which **sectors** are discussed (通信设备, 汽车零部件, 蓄电池, 数据处理)
- Note **trade balance arguments** (技术含量差异 → 差额原因)
- Cross-reference with the user’s 四矩阵 framework for asset allocation signals
