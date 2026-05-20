---
description: |
  使用卢麒元投资分析框架进行系统性宏观数据分析。
  采集CPI、M2、GDP、LPR、房价、股市等真实数据，
  计算真实通胀率和实质利率，定位四矩阵，判断策略阶段。
triggers:
  - 卢麒元
  - 宏观数据
  - 真实通胀率
  - 实质利率
  - 四矩阵
  - 金转油
  - 短股长金
  - CPI M2 GDP
  - 投资策略分析
  - 资产配置
name: luqiyuan-macro-analysis
---

# 卢麒元投资分析框架 - 宏观数据分析工作流

## 一、数据准备

### 1.1 环境准备
```bash
cd /home/coordinate35/macro_env
source .venv/bin/activate
python
```

### 1.2 导入依赖
```python
import akshare as ak
import pandas as pd
import json
from datetime import datetime
```

## 二、数据采集清单

| 指标 | AKShare接口 | 字段/处理 |
|------|------------|----------|
| CPI | `macro_china_cpi_monthly()` | `cpi`列最新值 |
| M2 | `macro_china_sh_m2()` | `moneySupplyM2`列最新同比 |
| GDP | `macro_china_gdp()` | `gdp`列最新同比 |
| LPR(5Y) | `macro_china_lpr()` | `LPR_5Y`列最新值 |
| 房价 | `macro_china_new_house_price()` | `同比`列最新值（需去首行） |
| 股市 | `stock_zh_index_spot_em()` | 上证指数`最新价` |

### 2.1 数据采集代码模板
```python
# CPI
df_cpi = ak.macro_china_cpi_monthly()
cpi = df_cpi["cpi"].iloc[-1]

# M2
df_m2 = ak.macro_china_sh_m2()
m2 = df_m2["moneySupplyM2"].iloc[-1]

# GDP
df_gdp = ak.macro_china_gdp()
gdp = df_gdp["gdp"].iloc[-1]

# LPR
df_lpr = ak.macro_china_lpr()
lpr = df_lpr["LPR_5Y"].iloc[-1]

# 房价（注意去首行非数据行）
df_house = ak.macro_china_new_house_price()
df_house = df_house.iloc[1:]
df_house["同比"] = pd.to_numeric(df_house["同比"], errors="coerce")
house = df_house["同比"].iloc[-1]

# 股市
df_stock = ak.stock_zh_index_spot_em()
sh_index = df_stock[df_stock["名称"]=="上证指数"]["最新价"].values[0]

# 汇总
result = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "CPI同比": cpi,
    "M2同比": m2,
    "GDP同比": gdp,
    "LPR_5Y": lpr,
    "房价同比": house,
    "上证指数": sh_index,
    "真实通胀率(M2法)": cpi + (m2 - gdp),
    "真实通胀率(配置法)": 0.6*cpi + 0.2*house + 0.2*float(sh_index)/100,
    "实质利率(LPR-真实通胀)": lpr - (cpi + (m2 - gdp)),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 三、核心计算体系

### 3.1 真实通胀率（双算法）

**算法A：货币供应量法（推荐）**
```
真实通胀率 = CPI + (M2增速 - GDP增速)
```

**算法B：资产配置法**
```
真实通胀率 = 60%×CPI + 20%×房价涨幅 + 20%×股市涨幅
```

### 3.2 实质利率
```
实质利率 = 名义利率 - 真实通胀率
实质负利率 = 真实通胀率 - 名义利率
```

### 3.3 临界点判断
| 实质负利率区间 | 含义 |
|--------------|------|
| >10% | 进入两位数，强避险信号 |
| 5-10% | 中高负利率，滞胀确认 |
| 0-5% | 边界负利率，观察区 |
| <0% | 实质正利率，股票/实体优先 |

## 四、四矩阵定位

基于**经济增长**和**通胀水平**两个维度：

| 状态 | 经济增长 | 通胀水平 | 实质负利率 | 投资策略 |
|:---:|:---:|:---:|:---:|:---:|
| **高高** | 高增长 | 高通胀 | 极高(10%+) | 🏠房地产 |
| **低高** | 低增长 | 高通胀 | 极高 | 🥇黄金/能源 |
| **高低** | 高增长 | 低通胀 | 低/正 | 📈股票/实体 |
| **低低** | 低增长 | 低通胀 | 较低 | 💰现金/债券 |

**当前策略演进（截至2026年5月）：**
- 2026年1月前："短股长金"——长期黄金为主
- **2026年1月起："金转油"——转向能源资产**
- 预计2026H2-2027H1：可能"油转股"或"油金并重"

## 五、金转油策略分析框架

### 5.1 成立条件（驱动逻辑）
1. **美元贬值趋势确立**：美债膨胀→美元信用削弱→美元计价大宗商品上涨
2. **能源价值回归**：ESG投资导致供给窄化+估值偏低+自由现金流改善
3. **黄金边际收益递减**：黄金牛市后"低垂果实"减少，能源相对空间更大

### 5.2 结束信号体系

| 信号 | 指标 | 阈值 |
|------|------|------|
| 美元贬值逆转 | DXY美元指数 | 突破105 |
| 能源估值过热 | 能源股市盈率 | >20倍 |
| 能源价格过热 | 布伦特原油 | >$100/桶 |
| 四矩阵转向 | GDP+通胀组合 | 实质利率转正或GDP破5%同时通胀下行 |
| 黑天鹅 | 日元汇率 | 突破150（日本向心坍缩） |

### 5.3 资产选择优先级
1. **高**：原油期货（CME/INE）——24小时连续定价
2. **中**：美股能源ETF——交易时间6.5h+盘前盘后
3. **低**：A股能源股——4h+T+1，跳空风险大

## 六、偏离观测与回归优兇（与 macroeconomic-system-modeling 衔接）

本框架的"真实通胀率"和"四矩阵"可以在多经济体 SFC 模型中进一步量化为Ω计价的偏离度和回归优先级。具体方法见 `macroeconomic-system-modeling` skill。

### 6.1 与Ω计价体系的对应

| 卢麒元概念 | 在多经济体 SFC 模型中的表达 |
|:---|:---|
| 真实通胀率 = CPI + (M2-GDP) | 篮子价格 B_i(t) 的变化率 ≈ CPI + (M2增速 - 实体资本增速) |
| 四矩阵决策 | 以 Ω 计价的高增/低增 × 高胀/低胀 |
| 短股长金 | "低高"状态下，黄金偏离度回归优先级最高 |
| 货币幻觉 | M2/B_i 上升 → 现金 Ω 价值蒸发 |
| 金转油 | 比较黄金与能源的 Ω 偏离度 + RPI |

### 6.2 实战应用流程

当进行跨国资产配置或判断某个市场是否被高估/低估时：
1. 先用本 skill 采集当前 CPI、M2、GDP、LPR、房价、股市数据
2. 计算真实通胀率和四矩阵位置
3. 若需要跨国比较或精细偏离量化，切换至 `macroeconomic-system-modeling`
4. 利用 RPI 判断多个偏离点中哪个最先回归，指导操作时机

## 七、美债数据补充

当分析美元贬值趋势时，需采集美债总额：

```python
import requests, re

url = "https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/debt-to-the-penny"
resp = requests.get(url, timeout=10)
# 提取最新美债总额，计算日均增量
```

或使用已知的 treasury API 直接获取最新数据。

## 七、输出格式

将分析结果保存为JSON + Markdown报告：
- 数据文件：`/home/coordinate35/hermes_data/macro_YYYYMMDD.json`
- 报告文件：`/home/coordinate35/hermes_data/macro_report_YYYYMMDD.md`

## 八、注意事项

1. **房价数据**：`macro_china_new_house_price()` 首行可能为非数据行（如"70个大中城市..."），需 `df.iloc[1:]` 去除
2. **LPR数据**：返回的是历史数据表，最新值在最后一行
3. **GDP发布频率**：季度数据，注意时间滞后
4. **M2数据**：月度发布，注意月末/月初更新时间
5. **策略时效性**：卢麒元策略会随国际货币格局调整，必须确认当前最新推荐（2026年1月起为"金转油"）
6. **验证优先**：分析用户提出的观点/数据前，先核实事实准确性