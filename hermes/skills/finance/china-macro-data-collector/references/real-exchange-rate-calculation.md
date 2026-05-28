# 人民币实际汇率计算（CNY/USD）

## 公式

```
实际汇率 (RER) = 名义汇率 (NER) × (P_US / P_CN)
```

其中 P_US 和 P_CN 分别是美国和中国的物价水平指数（同基期）。

## 数据源

| 数据 | 来源 | 方式 |
|:---|:---|:---|
| 名义汇率 (CNY/USD) | FRED `DEXCHUS` | `curl fredgraph.csv` |
| 美国 CPI | FRED `CPIAUCSL` | `curl fredgraph.csv` |
| 中国 CPI (YoY) | AKShare `macro_china_cpi()` | Python |

## 计算步骤

### 1. 获取名义汇率

```bash
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS&cosd=2026-05-01&coed=2026-05-31"
# 取最新一条
```

### 2. 获取美国 CPI 指数

```bash
# 基期和当前
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd=2020-01-01&coed=2020-01-31"
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd=2026-04-01&coed=2026-05-31"
# CPIAUCSL 是绝对指数（1982-84=100），直接用比值
us_ratio = cpi_now / cpi_base
```

### 3. 计算中国 CPI 累计指数

**坑：AKShare 的 `macro_china_cpi()` 返回的是同比（YoY），不是绝对指数。**

需要链式连乘：
```python
# 年度平均 YoY → 累计
annual_yoy = {2020: 2.51, 2021: 0.92, 2022: 1.96, ...}
cum = 1.0
for y in years:
    cum *= (1 + annual_yoy[y] / 100)
# 2026 部分年：按已过月数比例
partial = (1 + 2026_yoy/100) ** (months_elapsed/12)
cn_total = cum * partial
```

更精确的方式：用每年 1 月的 YoY 链式连乘（月频，但只需 1 月数据）。

### 4. 代入公式

```python
rer = nominal_rate * (us_ratio / cn_total)
```

## 已验证实例（2026-05-28）

| 指标 | 值 | 来源 |
|:---|:---|:---|
| 名义汇率 | 6.80 CNY/USD | FRED DEXCHUS 2026-05-22 |
| 美国 CPI (2020-01) | 259.127 | FRED CPIAUCSL |
| 美国 CPI (2026-04) | 332.407 | FRED CPIAUCSL |
| 美国累计通胀 | +28.3% | 计算 |
| 中国累计通胀 | +6.4% | AKShare 链式 |
| **实际汇率** | **8.20 CNY/USD** | 计算 |

**解读**：名义汇率从 7.0 升到 6.8（升值 2.9%），但美国通胀远超中国，导致实际汇率贬值约 17%。

## 卢麒元框架含义

- 中国 CPI 被结构性低估 → 实际通胀高于官方数据 → 实际汇率实际更弱
- 人民币"外购买力强、内购买力弱"的背离：对外名义升值，对内因通胀缩水
- 实际汇率贬值 → 出口竞争力增强，但资本外流压力加大
