---
name: us-macro-data-retrieval
description: >
  采集美国宏观经济数据：国债总量与持有人结构（TIC）、FRED 宏观指标（GDP/通胀/就业）、
  美联储资产负债表（H.4.1）。数据源均为官方一手，无需 API Key。
tags: [finance, us-macro, treasury, tic, fred, gdp, inflation, fed]
---

# 美国宏观数据采集

## 触发条件
- 用户询问美国国债、美债持有人、TIC 数据
- 用户询问美国 GDP、通胀、债务/GDP 比率
- 用户询问美联储持仓、缩表
- 用户需要美国数据用于卢麒元框架国际对比

## 数据源速查

| 数据类型 | 来源 | URL | 格式 | 频率 |
|:---|:---|:---|:---|:---|
| 美债总量 | Treasury FiscalData | `api.fiscaldata.treasury.gov/.../debt_to_penny` | JSON API | 每日 |
| 海外持有人 | TIC SLT Table 5 | `ticdata.treasury.gov/.../slt_table5.txt` | TSV | 月（滞后~2月） |
| 美联储持仓 | Fed H.4.1 | `federalreserve.gov/releases/h41/current/` | HTML | 每周 |
| GDP/通胀等 | FRED | `fred.stlouisfed.org/graph/fredgraph.csv` | CSV | 季度/月 |

---

## 1. 美国公共债务总量

**API：**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?sort=-record_date&page[size]=5
```
返回字段：`tot_pub_debt_out_amt`（总公共债务），`record_date`。

**指定日期查询：**
```
?filter=record_date:in:(2025-12-31,2026-03-31)&sort=record_date
```

---

## 2. TIC 海外持有人数据 ⚠️ 关键修正

### ❌ 旧源（已过时）
`https://ticdata.treasury.gov/Publish/mfh.txt` — 数据截止 2023年1月，不再更新。

### ✅ 当前源（SLT Table 5）
```
https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt
```
- 格式：**制表符分隔（TSV）**，不是固定宽度
- 最新数据：2026年3月（T+2月滞后）
- 包含：各国月度持仓 + 汇总行（Grand Total, Foreign Official, Treasury Bills/Bonds 分项）
- 数据单位：十亿美元（Billions of dollars）

**解析要点：**
- 前 4 行为元数据（标题、单位、链接），第 5 行为列头
- 汇总行（Grand Total / Of Which / All Other）混在数据中，需过滤
- 用 `split('\t')` 按制表符切割，不是固定列宽

**补充 HTML 版（可选）：**
```
https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.html
```
包含相同数据但用 `<td>` 标签包裹，可 grep `<td>2026-03</td>` 确认数据时效。

---

## 3. 美联储持仓（H.4.1）

**URL：** `https://www.federalreserve.gov/releases/h41/current/`

解析 HTML 查找 "U.S. Treasury securities" 所在行的数值（单位：百万美元）。

**注意事项：**
- H.4.1 页面加载较慢，优先用 `curl` + 正则解析
- 搜索模式：`Securities held outright` → `U.S. Treasury securities` → 找紧随的数值
- 值通常以 `$X,XXX,XXX`（百万）形式出现，需 ×1000 转换为十亿

---

## 4. FRED 宏观数据（无需 API Key）

**CSV 导出模板：**
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd={START}&coed={END}
```

### 常用序列

| 指标 | FRED 代码 | 频率 | 单位 |
|:---|:---|:---|:---|
| 名义 GDP | `GDP` | 季度 | 十亿美元，季调年化 |
| 实际 GDP | `GDPC1` | 季度 | 十亿美元（2017链式），季调年化 |
| GDP 平减指数 | `GDPDEF` | 季度 | 指数（2017=100） |
| CPI | `CPIAUCSL` | 月度 | 指数（1982-84=100） |
| PCE 物价指数 | `PCEPI` | 月度 | 指数（2017=100） |
| 失业率 | `UNRATE` | 月度 | % |
| 联邦基金利率 | `FEDFUNDS` | 月度 | % |

**参数说明：**
- `cosd` / `coed`：起止日期，格式 `YYYY-MM-DD`
- 无 `&` 前缀参数时直接追加 `?id=SERIES`，否则用 `&id=SERIES`
- 返回 CSV 含 `observation_date,VALUE` 两列

---

## 5. 数据交叉验证公式

### 名义GDP = 实际GDP × 平减指数
```
名义 GDP = 实际 GDP (GDPC1) × GDPDEF / 100
```
误差应在四舍五入范围内。每次都验算。

### GDP平减 vs CPI vs PCE
三个通胀指标不同，不要混用：

| 指标 | 覆盖范围 | 权重结构 | 特点 |
|:---|:---|:---|:---|
| GDP平减 | 仅国内生产 | 动态（Paasche） | 最低，不含进口通胀 |
| PCE | 消费（含进口） | 动态（Fisher） | 居中，美联储首选 |
| CPI | 城市消费者 | 固定（Laspeyres） | 最高，住房权重大 |

**常见模式：** CPI > PCE > GDP平减 → 进口/住房驱动型通胀。

---

## 6. 报告输出规范 ⚠️ 避坑

### 分母混淆问题
在讨论持有人占比时，**必须明确分母**：
- "海外持有中" = 分母是海外总持有（~$9T）
- "总债务中" = 分母是全部公共债务（~$39T）

❌ 错误示例："外国官方占 41.7%……（后来又说）占 10.0%"
✅ 正确示例："外国官方占海外持有的 41.7%，占总债务的 10.0%"

### 美债总量
总公共债务 ≠ 可流通债务。`debt_to_penny` 返回的是**总公共债务**（含政府内部持有），与 TIC 统计的可流通债务口径不同。引用时注明口径。

### QoQ 年化
FRED GDP 数据是**季调年化率**（SAAR），即季度值×4。计算 QoQ 时直接用原始值比较即可；如需年化增速，乘以 4。

---

## 参考链接
- [TIC 数据门户](https://ticdata.treasury.gov/)
- [FRED](https://fred.stlouisfed.org/)
- [Treasury FiscalData API](https://fiscaldata.treasury.gov/api-documentation/)
- [Fed H.4.1 发布](https://www.federalreserve.gov/releases/h41/)
