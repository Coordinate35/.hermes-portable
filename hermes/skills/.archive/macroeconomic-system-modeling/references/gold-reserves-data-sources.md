# 黄金储备数据采集指南

## 一、主数据源：世界黄金协会 (WGC)

**URL**: `https://www.gold.org/goldhub/data/gold-reserves-by-country`

### 访问方式
- **无需登录**即可查看 Snapshot 视图（最新季度前10名 + 区域树图）
- 展开完整列表需点击 "Show more countries" 按钮
- 下载 xlsx 需注册登录（免费）

### 浏览器提取方法（已验证可用，2026-06-23）

仪表板数据通过 JS 动态渲染，无需登录即可提取 Snapshot 视图的完整表格：

```javascript
// 步骤1：点击 "Show more countries" 展开完整列表
var btns = document.querySelectorAll('button');
for(var i=0; i<btns.length; i++) {
  if(btns[i].textContent.includes('more')) { btns[i].click(); }
}

// 步骤2：提取完整表格（含所有已展开国家）
Array.from(document.querySelectorAll('table tr'))
  .map(r => Array.from(r.querySelectorAll('td,th'))
    .map(c => c.textContent.trim()).join(' | '))
  .filter(s => s.length > 0).join('\n')
```

**注意**：未登录状态下只能看到 Snapshot 视图（最新季度），无法切换时间范围或下载历史数据。展开后约 100+ 行数据，包含所有已向 IMF 报告的国家。标记为 "AWAITED" 的国家表示数据尚未报告。

### 数据字段
| 字段 | 说明 |
|:---|:---|
| Country | 国家名 |
| Region | 区域分类（含 "Middle East & North Africa"） |
| Economic grouping | 收入分组 |
| FX Reserves | 外汇储备（百万美元） |
| Total Reserves | 总储备（百万美元） |
| Gold Reserves Tonnes | 黄金储备（吨） |
| Gold Reserves Millions | 黄金储备（百万美元） |
| Holdings % | 黄金占总储备百分比 |

### 更新频率
- 季度更新，滞后约2个月
- 最新数据：Q1 2026（截至2026-03-31），2026年6月发布

## 二、IMF IFS API（备用）

**URL**: `http://dataservices.imf.org/REST/SDMX_JSON.svc/`

- 从本机（coordinate35 的 Linux 环境）**网络不可达**（ERR_NAME_NOT_RESOLVED / Network unreachable）
- 浏览器也无法访问该域名
- 如需使用，需先解决网络连通性问题

## 三、中东国家数据盲区

### 已知问题
大部分中东国家是 **"late reporters"**，不按时向 IMF 报告黄金持仓：

**有数据的（Q1 2026）**：
- 利比亚：146.65 吨（20.40%）
- 埃及：129.51 吨（38.23%）
- 卡塔尔：115.23 吨（30.43%）

**数据待报（AWAITED）**：
沙特阿拉伯、阿联酋、科威特、伊拉克、巴林、阿曼、约旦、黎巴嫩、叙利亚、也门、阿尔及利亚、摩洛哥、突尼斯

### 间接观测方法
1. **瑞士海关月度黄金贸易数据**：中东买金主要通过瑞士中转，瑞士出口数据可间接追踪
2. **迪拜黄金交易所 (DGCX)**：期货合约交易数据
3. **Bloomberg/Reuters 终端**：主权基金配置变动新闻

## 四、瑞士海关黄金贸易数据（间接追踪中东买金）

中东国家购金主要通过瑞士精炼厂中转，瑞士黄金出口数据是追踪中东黄金流动的最佳间接指标。

### 数据源状态（2026-06-23 实测）

| 入口 | 状态 | 详情 |
|:---|:---|:---|
| Swiss Impex 旧系统 (gate.ezv.admin.ch) | ❌ 已下线 | 所有旧链接返回 404，系统已迁移 |
| BAZG 新网站 Swiss Impex | ❌ 需认证 | 需要 eIAM 联邦身份认证登录 |
| swissimpex.admin.ch | ❌ 被拦截 | CloudFront 403，从本机 IP 被拒 |
| UN Comtrade API 预览端点 | ❌ 空数据 | `/public/v1/preview/` 对瑞士 HS 7108 返回 count=0 |
| UN Comtrade API v1 | ❌ 需密钥 | 需要 Ocp-Apim-Subscription-Key |
| UN Comtrade 旧 API (comtrade.un.org) | ❌ 已迁移 | 重定向到 comtradeplus.un.org |
| OEC World (oec.world) | ❌ Cloudflare | JS challenge 拦截 |

### UN Comtrade API 探索记录

预览端点可连通但瑞士黄金数据为空：
```bash
# 连通但无数据
curl "https://comtradeapi.un.org/public/v1/preview/C/A/HS?cmdCode=7108&flowCode=X&reporterCode=756&period=2023"
# → {"count":0,"data":[]}

# v1 端点需要订阅密钥
curl "https://comtradeapi.un.org/data/v1/get/C/A/HS?cmdCode=7108&flowCode=X&reporterCode=756&period=2023" \
  -H "Ocp-Apim-Subscription-Key: public"
# → 401 Access denied
```

### 可行替代路径
1. 手动在 WGC 注册免费账号，下载完整 xlsx（含月度变动）
2. Bloomberg 终端拉瑞士海关黄金进出口数据
3. 解决了 Swiss Impex eIAM 认证后，可编写自动化脚本

## 五、其他尝试过但不可用的数据源

| 数据源 | 状态 | 原因 |
|:---|:---|:---|
| Wikipedia Gold Reserve | 不可用 | CDP 导航超时 |
| Trading Economics | 不可用 | 403 拒绝访问 |
| CEIC Data | 不可用 | 页面加载超时 |
| 中国国家统计局 | 不可用 | 403 IP 被封 |
