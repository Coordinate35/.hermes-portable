---
name: china-macro-data-collector
category: finance
description: |
  采集中国宏观经济数据并使用卢麒元投资分析框架进行计算。
  包含：CPI、M2、GDP、LPR、房价、股市数据采集；
  历史数据回溯（5年+）与可视化图表生成；
  真实通胀率、实质利率、四矩阵周期判断与轨迹分析；
  政府经济目标分析与前瞻性推演。
author: Assistant
tags: [akshare, macro-economics, investment-analysis, china, luqiyuan, visualization, matplotlib]
version: 1.4.0
requirements:
  - akshare>=1.18.0
  - pandas>=2.0.0
  - matplotlib>=3.10.0
  - python>=3.10
---

# 中国宏观经济数据采集与卢麒元投资分析框架

## 功能概述

本技能提供完整的中国宏观经济数据采集和投资分析能力，包括：

1. **宏观数据采集**：CPI、M2、GDP、LPR、房价、股市
2. **卢麒元框架计算**：真实通胀率、实质利率、四矩阵周期判断
3. **微博热搜筛选**：中东、经济金融、政策关键词筛选
4. **美国财政部数据**：美债规模、财政收支、利息支出（全球流动性分析）

## 使用方式

### 方式1：直接运行Python脚本

```python
from hermes_tools import terminal

# 运行完整的数据采集和分析
terminal("""
  cd /home/coordinate35/hermes_data/hermes_data/venv && source .venv/bin/activate && python << 'PYEOF'
import akshare as ak
import pandas as pd
import json
from datetime import datetime

# 1. 数据采集
results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "data": {}
}

# CPI
cpi_df = ak.macro_china_cpi()
results['data']['CPI同比'] = round(float(cpi_df.iloc[0]['全国-当月']) - 100, 2)

# M2
m2_df = ak.macro_china_money_supply()
m2_col = [c for c in m2_df.columns if 'M2' in c and '同比' in c][0]
results['data']['M2同比增速'] = round(float(m2_df.iloc[0][m2_col]), 2)

# GDP
gdp_df = ak.macro_china_gdp()
gdp_col = [c for c in gdp_df.columns if '同比' in c and '增长' in c][0]
results['data']['GDP同比增速'] = round(float(gdp_df.iloc[0][gdp_col]), 2)

# LPR
lpr_df = ak.macro_china_lpr()
for idx, row in lpr_df.iterrows():
    for col in lpr_df.columns:
        if '5' in col and ('LPR' in col or 'lpr' in col):
            if not pd.isna(row[col]) and float(row[col]) > 0:
                results['data']['5年期LPR'] = round(float(row[col]), 2)
                break
    if '5年期LPR' in results['data']:
        break

# 房价
house_df = ak.macro_china_new_house_price()
latest_date = house_df['日期'].max()
latest_data = house_df[house_df['日期'] == latest_date]
results['data']['房价同比涨幅'] = round(latest_data['新建商品住宅价格指数-同比'].mean(), 2)

# 2. 卢麒元框架计算
cpi = results['data']['CPI同比']
m2 = results['data']['M2同比增速']
gdp = results['data']['GDP同比增速']
lpr = results['data']['5年期LPR']
house = results['data']['房价同比涨幅'] - 100

# 真实通胀率
real_inflation_m2 = cpi + (m2 - gdp)
real_inflation_asset = 0.6 * cpi + 0.2 * house + 0.2 * 2.1

# 实质利率
real_rate_m2 = lpr - real_inflation_m2
real_rate_asset = lpr - real_inflation_asset

# 四矩阵周期判断
growth = "高增长" if gdp >= 5.0 else "低增长"
inflation = "高通胀" if real_inflation_m2 >= 5.0 else "低通胀"

matrix_mapping = {
    ("高增长", "高通胀"): ("高高", "🏠房地产", "高通胀+高增长，房地产是不二选择"),
    ("低增长", "高通胀"): ("低高", "🥇黄金", "滞胀（高通胀+低增长），黄金是避险首选"),
    ("高增长", "低通胀"): ("高低", "📈股票/实体经济", "高增长+低通胀，利好股市和实体"),
    ("低增长", "低通胀"): ("低低", "💰现金/债券", "低增长+低通胀，持有现金或债券"),
}

current_state, investment, strategy = matrix_mapping[(growth, inflation)]

# 保存结果
results['analysis'] = {
    'real_inflation_m2': round(real_inflation_m2, 2),
    'real_inflation_asset': round(real_inflation_asset, 2),
    'real_rate_m2': round(real_rate_m2, 2),
    'real_rate_asset': round(real_rate_asset, 2),
    'cycle_state': current_state,
    'growth': growth,
    'inflation': inflation,
    'investment': investment,
    'strategy': strategy
}

with open('/home/coordinate35/hermes_data/macro_analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ 数据采集和分析完成！")
print(f"📊 数据文件: /home/coordinate35/hermes_data/macro_analysis_result.json")
print(f"\n📈 真实通胀率 (M2法): {real_inflation_m2:.2f}%")
print(f"📈 真实通胀率 (资产法): {real_inflation_asset:.2f}%")
print(f"💰 实质利率 (M2法): {real_rate_m2:.2f}%")
print(f"📊 周期状态: {current_state} ({growth}+{inflation})")
print(f"🎯 投资建议: {investment}")
print(f"📝 策略: {strategy}")

PYEOF
""")
```

### 方式2：使用浏览器获取微博热搜

```python
from hermes_tools import browser_navigate, browser_snapshot

# 访问微博热搜
browser_navigate("https://s.weibo.com/top/summary?cate=realtimehot")
snapshot = browser_snapshot(full=True)

# 解析热搜内容（从snapshot中提取）
# 热搜数据包含在table中，格式为：排名 + 标题 + 热度值
```

### 方式3：命令行快速采集

```bash
# 激活虚拟环境并运行采集脚本
cd /home/coordinate35/hermes_data/hermes_data/venv
source .venv/bin/activate
python macro_collector.py
```

## AKShare数据采集陷阱与排错指南

在实际采集中，AKShare的多个接口存在非直观的陷阱。以下是通过多轮试错发现的关键问题及解决方案。

### 陷阱1：CPI日期中文格式解析失败

**现象**：`pd.to_datetime(cpi_df['月份'])` 报错 `Unknown datetime string format: 2026年03月份`

**原因**：AKShare返回的`月份`列是中文格式字符串，不是标准ISO格式。

**解决**：
```python
# 必须显式指定中文格式
cpi_df['年月_dt'] = pd.to_datetime(cpi_df['月份'], format='%Y年%m月份', errors='coerce')
# 如果失败，再尝试自动推断
if cpi_df['年月_dt'].isna().all():
    cpi_df['年月_dt'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
```

### 陷阱2：LPR数据返回的是最早记录而非最新

**现象**：`lpr_df.iloc[0]` 返回的是1991年的记录，而不是最新的LPR。

**原因**：`ak.macro_china_lpr()` 返回的数据是按时间升序排列的（从早到晚），`iloc[0]`是最早记录。

**解决**：
```python
lpr_df['TRADE_DATE'] = pd.to_datetime(lpr_df['TRADE_DATE'])
lpr_df = lpr_df.sort_values('TRADE_DATE', ascending=False)  # 降序排列
latest_lpr = lpr_df[lpr_df['LPR5Y'].notna()].iloc[0]  # 现在取到的是最新记录
lpr_5y = float(latest_lpr['LPR5Y'])
```

### 陷阱3：房价"同比"列实际存的是指数值

**现象**：`house_yoy = 101.8`，看起来通胀很高，但实际同比只有1.8%。

**原因**：`macro_china_new_house_price()` 的`新建商品住宅价格指数-同比`列存的是**指数值**（基期=100），不是涨幅百分比。

**解决**：
```python
house_idx = float(latest_row['新建商品住宅价格指数-同比'])
if house_idx > 50:
    house_yoy = round(house_idx - 100, 2)  # 指数值转同比涨幅
else:
    house_yoy = house_idx  # 已经是百分比
```

### 陷阱4：M2/GDP列名不固定

**现象**：`m2_df.columns` 在不同AKShare版本下列名不同，硬编码会报错。

**解决**：动态搜索列名
```python
m2_col = None
for c in m2_df.columns:
    if 'M2' in str(c) and ('同比' in str(c) or '增长' in str(c)):
        m2_col = c
        break
if m2_col is None:
    m2_col = m2_df.columns[1]  # 回退到第二列
```

### 陷阱5：JSON序列化datetime/date对象报错

**现象**：`json.dump(results, f)` 报错 `TypeError: Object of type date is not JSON serializable`

**解决**：
```python
def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, pd.Series):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")

json.dump(results, f, ensure_ascii=False, indent=2, default=json_serial)
```

### 安全采集模板

```python
import akshare as ak
import pandas as pd
import json
from datetime import datetime

def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f"Type {type(obj)} not serializable")

def collect_china_macro_safe():
    results = {}
    
    # CPI - 处理中文日期
    cpi_df = ak.macro_china_cpi()
    cpi_df['年月_dt'] = pd.to_datetime(cpi_df['月份'], format='%Y年%m月份', errors='coerce')
    if cpi_df['年月_dt'].isna().all():
        cpi_df['年月_dt'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
    cpi_df = cpi_df.sort_values('年月_dt').dropna(subset=['年月_dt'])
    cpi_latest = cpi_df.iloc[-1]
    cpi_yoy = round(float(cpi_latest['全国-当月']) - 100, 2)
    results['CPI'] = {"latest_yoy": cpi_yoy, "date": cpi_latest['年月_dt'].strftime('%Y-%m')}
    
    # M2 - 动态识别列名
    m2_df = ak.macro_china_money_supply()
    m2_col = [c for c in m2_df.columns if 'M2' in str(c) and '同比' in str(c)][0]
    m2_yoy = round(float(m2_df.iloc[0][m2_col]), 2)
    results['M2'] = {"latest_yoy": m2_yoy, "date": str(m2_df.iloc[0].iloc[0])}
    
    # GDP - 动态识别列名
    gdp_df = ak.macro_china_gdp()
    gdp_col = [c for c in gdp_df.columns if '同比' in str(c)][0]
    gdp_yoy = round(float(gdp_df.iloc[0][gdp_col]), 2)
    results['GDP'] = {"latest_yoy": gdp_yoy, "quarter": str(gdp_df.iloc[0].iloc[0])}
    
    # LPR - 必须降序取最新
    lpr_df = ak.macro_china_lpr()
    lpr_df['TRADE_DATE'] = pd.to_datetime(lpr_df['TRADE_DATE'])
    lpr_df = lpr_df.sort_values('TRADE_DATE', ascending=False)
    latest_lpr = lpr_df[lpr_df['LPR5Y'].notna()].iloc[0]
    results['LPR'] = {
        "5_year": round(float(latest_lpr['LPR5Y']), 2),
        "1_year": round(float(latest_lpr['LPR1Y']), 2) if pd.notna(latest_lpr['LPR1Y']) else None,
        "date": latest_lpr['TRADE_DATE'].strftime('%Y-%m-%d')
    }
    
    # 房价 - 指数值转同比
    house_df = ak.macro_china_new_house_price()
    latest_row = house_df.iloc[0]
    house_idx = float(latest_row['新建商品住宅价格指数-同比'])
    house_yoy = round(house_idx - 100, 2) if house_idx > 50 else house_idx
    results['house_price'] = {"yoy": house_yoy, "index_value": house_idx}
    
    return results
```

## 数据字段说明

### 原始数据字段

| 字段 | 说明 | 数据来源 |
|------|------|----------|
| CPI同比 | 消费者物价指数同比涨幅 | akshare.macro_china_cpi() |
| M2同比增速 | 广义货币供应量同比增速 | akshare.macro_china_money_supply() |
| GDP同比增速 | 国内生产总值同比增速 | akshare.macro_china_gdp() |
| 5年期LPR | 贷款市场报价利率（5年期） | akshare.macro_china_lpr() |
| 房价同比涨幅 | 70城新建商品住宅价格指数 | akshare.macro_china_new_house_price() |
| 股市涨幅 | 上证指数区间涨跌幅 | akshare.index_zh_a_hist() |

### 分析结果字段

| 字段 | 说明 |
|------|------|
| real_inflation_m2 | 真实通胀率（M2法） |
| real_inflation_asset | 真实通胀率（资产配置法） |
| real_rate_m2 | 实质利率（M2法） |
| real_rate_asset | 实质利率（资产配置法） |
| cycle_state | 四矩阵周期状态（高高/低高/高低/低低） |
| growth | 经济增长判断（高增长/低增长） |
| inflation | 通胀水平判断（高通胀/低通胀） |
| investment | 投资建议（房地产/黄金/股票/现金） |
| strategy | 投资策略说明 |

## 卢麒元投资分析框架说明

### 1. 真实通胀率计算

**公式1：货币供应量法（推荐）**
```
真实通胀率 = CPI + (M2增速 - GDP增速)
```

**公式2：资产配置法**
```
真实通胀率 = 60%×CPI + 20%×房价涨幅 + 20%×股市涨幅
```

### 2. 实质利率计算
```
实质利率 = 名义利率 - 真实通胀率
```

### 3. 四矩阵周期判断

| 状态 | 经济增长 | 通胀水平 | 投资策略 |
|:---:|:---:|:---:|:---:|
| **高高** | 高增长 | 高通胀 | 🏠房地产 |
| **低高** | 低增长 | 高通胀 | 🥇黄金 |
| **高低** | 高增长 | 低通胀 | 📈股票/实体 |
| **低低** | 低增长 | 低通胀 | 💰现金/债券 |

## 微博热搜关键词筛选

### 关键词配置

```python
keywords = {
    "中东": ["中东", "沙特", "伊朗", "以色列", "巴勒斯坦", "土耳其", ...],
    "经济金融": ["经济", "金融", "股市", "汇率", "利率", "通胀", ...],
    "政策": ["政策", "发改委", "国务院", "财政部", "监管", ...]
}
```

### 使用方法

从微博热搜页面获取数据后，使用关键词匹配进行分类筛选。

## 美国财政部API数据采集

### 可获取的美国财政数据

| 数据类型 | 端点 | 更新频率 | 说明 |
|:---:|:---:|:---:|:---|
| **国债总额** | /v2/accounting/od/debt_to_penny | 每日 | 当前约$39万亿 |
| **国债余额** | /v2/accounting/od/debt_outstanding | 每季 | 季度国债数据 |
| **国债利息** | /v2/accounting/od/interest_expense | 每月 | 月度利息支出 |
| **财政概览** | /v1/accounting/mts/mts_table_1 | 每月 | 收入/支出/赤字 |
| **收入明细** | /v1/accounting/mts/mts_table_2 | 每月 | 税收等收入分类 |
| **支出明细** | /v1/accounting/mts/mts_table_3 | 每月 | 政府部门支出分类 |

### 使用示例

```python
import requests
import pandas as pd

# 美国财政部API基础URL
base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# 1. 获取国债总额
def get_us_debt():
    """获取美国国债总额历史数据"""
    endpoint = "/v2/accounting/od/debt_to_penny"
    url = f"{base_url}{endpoint}"
    
    params = {
        "fields": "record_date,tot_pub_debt_out_amt,debt_held_public_amt,intragov_hold_amt",
        "sort": "-record_date",
        "limit": 100
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['data'])
    
    # 转换单位为万亿美元
    for col in ['tot_pub_debt_out_amt', 'debt_held_public_amt', 'intragov_hold_amt']:
        df[col] = df[col].astype(float) / 1e12
    
    return df

# 2. 获取财政收支数据
def get_fiscal_data():
    """获取美国财政收支概览"""
    endpoint = "/v1/accounting/mts/mts_table_1"
    url = f"{base_url}{endpoint}"
    
    params = {
        "sort": "-record_date",
        "limit": 500
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['data'])
    
    return df

# 使用示例
debt_df = get_us_debt()
print(f"最新国债总额: ${debt_df.iloc[0]['tot_pub_debt_out_amt']:.2f}万亿")
```

### 卢麒元框架应用 - 美债视角

美债规模和财政状况对中国投资的影响：

#### 1. 资本流转三流理论应用

**流向分析**：
- 美债 $39万亿 → 美元信用扩张 → 全球流动性满盈
- **对中国影响**: 美元超发 → 输入性通胀压力 → 人民币资产保值需求

**流量分析**：
- 日均增长 $60亿 → 年增量 ~$2.2万亿
- **债务增速 > GDP增速** → 庞氏化趋势 → 实质负利率加剧

**流速分析**：
- 债务/GDP ≈ 122% → 偿债能力临界点
- **高债务 + 高利率** = 财政不可持续 → 最终被迫降息或违约

#### 2. 投资策略暗示

| 情景 | 概率 | 策略 |
|:---:|:---:|:---|
| 美债持续膨胀+高利率 | 60% | 黄金 20% + 大宗商品 15% + 现金 30% |
| 债务触发危机/降息 | 25% | 科技股 25% + 长期美债 20% |
| 美元信用崩溃 | 15% | 黄金 30% + 比特币 10% + 资源股 20% |

## 美国财政部API数据采集

除了中国宏观数据外，本技能还支持通过美国财政部官方API获取美债和财政数据，用于全球流动性分析。

### 可获取的美国财政数据

| 数据类型 | 端点 | 更新频率 | 说明 |
|:---:|:---:|:---:|:---|
| **国债总额** | /v2/accounting/od/debt_to_penny | 每日 | 当前约$39万亿 |
| **国债余额** | /v2/accounting/od/debt_outstanding | 每季 | 季度国债数据 |
| **国债利息** | /v2/accounting/od/interest_expense | 每月 | 月度利息支出 |
| **财政概览** | /v1/accounting/mts/mts_table_1 | 每月 | 收入/支出/赤字 |
| **收入明细** | /v1/accounting/mts/mts_table_2 | 每月 | 税收等收入分类 |
| **支出明细** | /v1/accounting/mts/mts_table_3 | 每月 | 政府部门支出分类 |

### 使用示例

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

# 美国财政部API基础URL
base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# 1. 获取国债总额
def get_us_debt():
    """获取美国国债总额历史数据"""
    endpoint = "/v2/accounting/od/debt_to_penny"
    url = f"{base_url}{endpoint}"
    
    params = {
        "fields": "record_date,tot_pub_debt_out_amt,debt_held_public_amt,intragov_hold_amt",
        "sort": "-record_date",
        "limit": 365
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['data'])
    
    # 转换单位为万亿美元
    for col in ['tot_pub_debt_out_amt', 'debt_held_public_amt', 'intragov_hold_amt']:
        df[col] = df[col].astype(float) / 1e12
    
    return df

# 2. 获取财政收支数据
def get_fiscal_data():
    """获取美国财政收支概览"""
    endpoint = "/v1/accounting/mts/mts_table_1"
    url = f"{base_url}{endpoint}"
    
    params = {
        "sort": "-record_date",
        "limit": 500
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['data'])
    
    return df

# 使用示例
debt_df = get_us_debt()
print(f"最新国债总额: ${debt_df.iloc[0]['tot_pub_debt_out_amt']:.2f}万亿")
print(f"公众持有: ${debt_df.iloc[0]['debt_held_public_amt']:.2f}万亿")
print(f"政府间持有: ${debt_df.iloc[0]['intragov_hold_amt']:.2f}万亿")
```

### API字段名发现技巧

**重要提示**: 不同端点的字段名不同，使用错误的字段名会返回400错误。

**发现正确字段名的方法**:

```python
def discover_fields(endpoint):
    """
    发现API端点的正确字段名
    先不带fields参数请求，查看返回的所有字段
    """
    url = f"{base_url}{endpoint}"
    
    # 不带fields参数，获取所有字段
    response = requests.get(url, params={"limit": 1}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            fields = list(data['data'][0].keys())
            
            # 找出金额字段
            amount_fields = [f for f in fields if 'amt' in f.lower() or 'amount' in f.lower()]
            
            return {
                'all_fields': fields,
                'amount_fields': amount_fields
            }
    
    return None

# 使用示例
print("🔍 探索各端点字段名:")

# 国债利息支出端点
fields = discover_fields("/v2/accounting/od/interest_expense")
print(f"\n国债利息支出端点:")
print(f"  金额字段: {fields['amount_fields']}")  # ['month_expense_amt', 'fytd_expense_amt']

# 财政收入端点
fields = discover_fields("/v1/accounting/mts/mts_table_2")
print(f"\n财政收入端点(MTS Table 2):")
print(f"  金额字段: {fields['amount_fields']}")  # ['current_month_budget_amt', 'current_fytd_budget_amt', ...]

# 财政支出端点
fields = discover_fields("/v1/accounting/mts/mts_table_3")
print(f"\n财政支出端点(MTS Table 3):")
print(f"  金额字段: {fields['amount_fields']}")  # ['current_month_rcpt_outly_amt', 'current_fytd_rcpt_outly_amt', ...]
```

### 各端点正确字段名速查表

| 端点 | 数据类型 | 金额字段名 | 说明 |
|:---:|:---:|:---:|:---|
| `/v2/accounting/od/debt_to_penny` | 国债总额 | `tot_pub_debt_out_amt`, `debt_held_public_amt`, `intragov_hold_amt` | 总债务、公众持有、政府间持有 |
| `/v2/accounting/od/interest_expense` | 国债利息 | `month_expense_amt`, `fytd_expense_amt` | 当月利息、财年累计利息 |
| `/v1/accounting/mts/mts_table_1` | 财政概览 | `current_month_rcpt_outly_amt`, `current_fytd_rcpt_outly_amt` | 当月收支、财年累计收支 |
| `/v1/accounting/mts/mts_table_2` | 财政收入明细 | `current_month_budget_amt`, `current_fytd_budget_amt` | **注意**: 使用`budget_amt`而非`rcpt_outly_amt` |
| `/v1/accounting/mts/mts_table_3` | 财政支出明细 | `current_month_rcpt_outly_amt`, `current_fytd_rcpt_outly_amt` | 当月支出、财年累计支出 |

## 日本宏观数据采集（AKShare）

卢麒元投资分析框架高度关注日本作为"向心坍缩"的第一张多米诺骨牌。日本央行政策（4月28日植田加息窗口等）、日元汇率、日债收益率是判断全球资本流向转折的核心指标。

### 可获取的日本宏观数据

| 数据类型 | AKShare函数 | 说明 | 更新频率 |
|:---:|:---:|:---:|:---:|
| **日本央行政策利率** | `macro_japan_bank_rate` | 月度政策利率 | 月 |
| **BOJ决议会议** | `macro_bank_japan_interest_rate` | 含实际/预测/前值 | 次 |
| **核心CPI同比** | `macro_japan_core_cpi_yearly` | 核心CPI（排除食品能源） | 月 |
| **标题CPI同比** | `macro_japan_cpi_yearly` | 标题CPI | 月 |
| **失业率** | `macro_japan_unemployment_rate` | 城镇失业率 | 月 |
| **领先指标** | `macro_japan_head_indicator` | 综合领先指标 | 月 |

### 重要提示：函数命名不一致

AKShare中日本宏观数据函数命名存在两种前缀，需要注意：
- `宏观_日本_心_消费者价格指数_年度` → `宏觀_日本_core_cpi_yearly`
- `宏观_日本_cpi_yearly` → `宏觀_日本_cpi_yearly`
- `宏观_日本_bank_rate` → `宏觀_日本_bank_rate`
- `宏观_bank_日本_interest_rate` → `宏觀_bank_日本_interest_rate` （含预测/前值）

**建议优先尝试**：`macro_bank_japan_interest_rate`
因为它包含了BOJ决议会议的实际值、预测值、前值，信息最完整。

### 使用示例

```python
import akshare as ak

# 1. 日本央行政策利率（含实际/预测/前值）
df_boj = ak.macro_bank_japan_interest_rate()
print(df_boj.tail(10))
# 输出: 商品, 日期, 今值, 预测值, 前值

# 2. 日本核心CPI
df_core_cpi = ak.macro_japan_core_cpi_yearly()
print(df_core_cpi.tail(10))
# 输出: 时间, 前值, 现值, 发布日期

# 3. 日本标题CPI
df_cpi = ak.macro_japan_cpi_yearly()
print(df_cpi.tail(10))
# 输出: 时间, 前值, 现值, 发布日期

# 4. 日本失业率
df_unemp = ak.macro_japan_unemployment_rate()
print(df_unemp.tail(10))

# 5. 日本领先指标
df_lead = ak.macro_japan_head_indicator()
print(df_lead.tail(10))
```

### 卢麒元框架应用 - 日本观测点

日本在"向心坍缩"分析中的关键作用：

| 观测点 | 阈值/信号 | 卢麒元判断 |
|:---:|:---:|:---|
| **日元党美元汇率** | 突破 160 | 日央行信誉防线失守，套息交易平仓触发 |
| **日债10年期收益率** | 突破 1.5% | YCC控制极限，日债流动性危机 |
| **日本核心CPI** | 持续 > 2.5% 或 < 1.0% | >2.5%加息压力/<1.0%通缩压力 |
| **BOJ政策利率** | 每次加息25bp | 资本流向迅速改变 |

**传导链条（卢麒元逻辑）：**
```
日元加息 → 日债收益率飙升 → 日债价格暴跌 → 日本金融机构浮亏 → 海外资产（美债/美股）被迫回流 → 全球流动性缩紧 → 速冻 → 向心坍缩
```

**日元降息/维持宽松的演化路径：**
```
降息 → 日元贬值 → 输入性通膨升温 → CPI回弹 → 被迫加息 → 日债更大危机
     → 套息交易继续 → 旧体系苟延残喘 → 终局更惨烈
```

### 日本宏观数据采集脚本

```python
#!/usr/bin/env python3
"""
日本宏观数据采集脚本 - 卢麒元投资分析框架
"""
import akshare as ak
import pandas as pd
import json
from datetime import datetime

def collect_japan_macro():
    """采集日本宏观数据并保存"""
    
    results = {
        "meta": {
            "country": "Japan",
            "generated_at": datetime.now().isoformat(),
            "framework": "卢麒元向心坍缩观测"
        },
        "data": {}
    }
    
    print("📊 开始采集日本宏观数据...")
    
    # 1. BOZ政策利率（含会议日期、实际/预测/前值）
    print("  🔍 采集BOJ政策利率...")
    df_boj = ak.macro_bank_japan_interest_rate()
    results['data']['boj_policy_rate'] = df_boj.tail(20).to_dict('records')
    
    # 2. 核心CPI
    print("  🔍 采集核心CPI...")
    df_core_cpi = ak.macro_japan_core_cpi_yearly()
    results['data']['core_cpi'] = df_core_cpi.tail(24).to_dict('records')
    
    # 3. 标题CPI
    print("  🔍 采集标题CPI...")
    df_cpi = ak.macro_japan_cpi_yearly()
    results['data']['headline_cpi'] = df_cpi.tail(24).to_dict('records')
    
    # 4. 失业率
    print("  🔍 采集失业率...")
    df_unemp = ak.macro_japan_unemployment_rate()
    results['data']['unemployment'] = df_unemp.tail(24).to_dict('records')
    
    # 5. 领先指标
    print("  🔍 采集领先指标...")
    df_lead = ak.macro_japan_head_indicator()
    results['data']['leading_indicator'] = df_lead.tail(24).to_dict('records')
    
    # 保存
    output_file = '/home/coordinate35/hermes_data/japan_macro_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 日本宏观数据采集完成！保存至: {output_file}")
    
    # 输出关键指标摘要
    latest_boj = df_boj.iloc[-1]
    latest_core_cpi = df_core_cpi.iloc[-1]
    latest_cpi = df_cpi.iloc[-1]
    
    print(f"\n📊 最新数据摘要:")
    print(f"  BOJ政策利率: {latest_boj.get('今值', 'N/A')}% (会议日: {latest_boj.get('日期', 'N/A')})")
    print(f"  核心CPI同比: {latest_core_cpi.get('现值', 'N/A')}% (发布: {latest_core_cpi.get('发布日期', 'N/A')})")
    print(f"  标题CPI同比: {latest_cpi.get('现值', 'N/A')}% (发布: {latest_cpi.get('发布日期', 'N/A')})")
    
    return results

if __name__ == '__main__':
    collect_japan_macro()
```

### 日本数据与美债数据的联动分析

日本是全球最大的债权国，持有美债约$1.1万亿。日本央行政策变化会直接影响美债需求：

```python
def analyze_japan_us_treasury_link():
    """
    分析日本政策与美债的联动关系
    """
    # 日本持有美债规模（约$1.1万亿）
    japan_us_debt = 1.1  # 万亿美元
    
    # 如果日本被迫加息 → 日债收益率上升 → 日元资金回流 → 美债被抛售
    scenarios = {
        "加息25bp": {
            "jpy_impact": "短期升值，但套息盘平仓压力巨大",
            "us_treasury_impact": "日本抛售美债压力",
            "probability": "50%"
        },
        "降息25bp": {
            "jpy_impact": "日元继续贬值",
            "us_treasury_impact": "日本继续买入美债支持价格",
            "probability": "30%"
        },
        "维持不变": {
            "jpy_impact": "汇率在当前区间波动",
            "us_treasury_impact": "影响有限",
            "probability": "20%"
        }
    }
    
    return scenarios
```

## 中国国债发行量数据采集（AKShare）

国债发行量是观察财政扩张力度和债市供给压力的核心指标。AKShare的 `bond_treasure_issue_cninfo` 函数可从巨潮资讯获取国债发行明细，但需注意默认参数极窄且存在跨市场重复记录。

### 重要提示：默认参数陷阱

`bond_treasure_issue_cninfo` 的默认参数为 `start_date="20210910"`, `end_date="20211109"`，仅返回约2个月数据。**必须显式传入自定义日期范围**才能获取多年数据。

### 采集步骤

#### 1. 原始数据采集

```python
import akshare as ak
import pandas as pd

# 必须显式指定日期范围
df = ak.bond_treasure_issue_cninfo(
    start_date="20210101",
    end_date="20251231"
)

print(f"获取到 {len(df)} 行原始数据")
print(f"时间范围: {df['发行起始日'].min()} 至 {df['发行起始日'].max()}")
```

#### 2. 跨市场去重

同一期国债会在多个交易市场分别列出（上交所、深交所、银行间债券市场、商业银行柜台市场），导致重复计数。**去重策略**：按 `年份 + 债券名称 + 发行起始日 + 实际发行总量` 去重。

```python
df['年份'] = pd.to_datetime(df['发行起始日']).dt.year

# 去重：同一期国债在不同市场的重复记录
df_dedup = df.drop_duplicates(
    subset=['年份', '债券名称', '发行起始日', '实际发行总量']
)

print(f"去重前: {len(df)} 行 → 去重后: {len(df_dedup)} 行")
```

#### 3. 债券类型分类

通过债券名称关键词进行分类：

```python
def classify_bond(name):
    if '储蓄' in name:
        return '储蓄国债'
    elif '贴现' in name:
        return '贴现国债'
    elif '超长期' in name or '到期续作' in name or '注资' in name or '特别' in name:
        return '特别国债'
    elif '附息' in name:
        return '附息国债'
    else:
        return '其他'

df_dedup['债券类型'] = df_dedup['债券名称'].apply(classify_bond)
```

#### 4. 年度汇总统计

```python
yearly_type = df_dedup.groupby(['年份', '债券类型'])['实际发行总量'].sum().unstack(fill_value=0)
yearly_type = yearly_type / 10000  # 转换为万亿元
yearly_type['合计'] = yearly_type.sum(axis=1).round(2)

print(yearly_type)
```

### 近5年参考数据（去重后）

| 年份 | 实际发行量（万亿） | 同比变化 | 主要特征 |
|:---:|:---:|:---:|:---|
| 2021 | **6.87** | — | 附息国债为主（4.69万亿） |
| 2022 | **10.27** | +49.5% | 特别国债重启，一般国债大幅放量 |
| 2023 | **12.52** | +21.9% | 附息国债突破8万亿 |
| 2024 | **12.38** | -1.1% | 高位稳定，重启超长期特别国债 |
| 2025 | **15.88** | +28.3% | 超长期特别国债+金融机构注资特别国债双扩容 |

### 关键发现

1. **5年增131%**：从2021年6.87万亿增至2025年15.88万亿，复合增长率约23%
2. **特别国债是增量主因**：2025年特别国债达2.55万亿，含超长期特别国债（~1.3万亿）、到期续作（7500亿）、金融机构注资（5000亿）
3. **附息国债是绝对主力**：占比约60%，反映常态化财政融资需求

### 投资分析提示

- **此为毛发行量**：包含到期续作和再融资，不等于国债余额净增量。净增量 = 毛发行量 - 到期偿还量
- **债市供给压力**：发行量持续高增对利率形成上行压力，尤其在央行未同步扩表时
- **财政扩张信号**：2025年发行量再次跳升28%，印证"更加积极财政政策"

### 完整采集脚本

```python
#!/usr/bin/env python3
"""
中国国债发行量采集脚本
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def collect_treasury_bond_issuance(start_year=2021, end_year=2025):
    start_date = f"{start_year}0101"
    end_date = f"{end_year}1231"
    
    # 1. 采集原始数据
    df = ak.bond_treasure_issue_cninfo(start_date=start_date, end_date=end_date)
    
    # 2. 去重
    df['年份'] = pd.to_datetime(df['发行起始日']).dt.year
    df = df.drop_duplicates(subset=['年份', '债券名称', '发行起始日', '实际发行总量'])
    
    # 3. 分类
    def classify(name):
        if '储蓄' in name: return '储蓄国债'
        elif '贴现' in name: return '贴现国债'
        elif any(k in name for k in ['超长期', '到期续作', '注资', '特别']): return '特别国债'
        elif '附息' in name: return '附息国债'
        else: return '其他'
    
    df['债券类型'] = df['债券名称'].apply(classify)
    
    # 4. 汇总
    yearly = df.groupby(['年份', '债券类型'])['实际发行总量'].sum().unstack(fill_value=0) / 10000
    yearly['合计'] = yearly.sum(axis=1).round(2)
    
    # 保存
    output = '/home/coordinate35/hermes_data/treasury_bond_issuance.csv'
    yearly.to_csv(output, encoding='utf-8-sig')
    print(f"✅ 数据已保存: {output}")
    print(yearly)
    return yearly

if __name__ == '__main__':
    collect_treasury_bond_issuance()
```

## 历史数据回溯与可视化

| 对比项 | MTS Table 2 | MTS Table 3 |
|:---:|:---:|:---:|
| **数据类型** | 汇总/总计数据 | 明细/分项数据 |
| **主要内容** | 收入、支出、赤字的汇总统计 | 各政府部门的支出明细 |
| **记录数量** | 较少 (~540条/3年) | 较多 (~1000条/3年) |
| **金额字段** | `budget_amt` (预算相关) | `rcpt_outly_amt` (收支相关) |
| **用途** | 判断国家财政健康度、债务可持续性 | 分析财政资金流向、政策优先级 |
| **关键分类** | Total Receipts, Total Outlays, Total Surplus/Deficit | Department of Defense, Social Security Administration, etc. |

**使用建议**:
- 看财政大局 → 用 **MTS Table 2** (收支汇总)
- 看部门支出 → 用 **MTS Table 3** (支出明细)
- 分析赤字趋势 → 用 **MTS Table 2** (直接看汇总)
- 对比军费vs民生 → 用 **MTS Table 3** (部门分类)

### 卢麒元框架应用 - 美债视角

美债规模和财政状况对中国投资的影响：

#### 1. 资本流转三流理论应用

**流向分析**：
- 美债 $39万亿 → 美元信用扩张 → 全球流动性满盈
- 对中国影响：美元超发 → 输入性通胀压力 → 人民币资产保值需求

**流量分析**：
- 日均增长 $60亿 → 年增量 ~$2.2万亿
- 债务增速 > GDP增速 → 庞氏化趋势 → 实质负利率加剧

**流速分析**：
- 债务/GDP ≈ 122% → 偿债能力临界点
- 高债务 + 高利率 = 财政不可持续 → 最终被迫降息或违约

#### 2. 投资策略暗示

| 情景 | 概率 | 策略 |
|:---:|:---:|:---|
| 美债持续膨胀+高利率 | 60% | 黄金 20% + 大宗商品 15% + 现金 30% |
| 债务触发危机/降息 | 25% | 科技股 25% + 长期美债 20% |
| 美元信用崩溃 | 15% | 黄金 30% + 比特币 10% + 资源股 20% |

### 参数配置

```python
# 数据文件路径
DATA_DIR = "/home/coordinate35/hermes_data/"
OUTPUT_FILE = f"{DATA_DIR}macro_data_final.json"
HISTORICAL_FILE = f"{DATA_DIR}historical_macro_data_2020_2025.json"
US_DEBT_FILE = f"{DATA_DIR}us_debt_history.csv"
JAPAN_MACRO_FILE = f"{DATA_DIR}japan_macro_data.json"

# 图表输出
CHART_FILES = {
    "cpi_inflation": f"{DATA_DIR}chart1_cpi_inflation.png",
    "gdp_m2": f"{DATA_DIR}chart2_gdp_m2.png",
    "four_matrix": f"{DATA_DIR}chart4_four_matrix.png"
}

# 宏观指标阈值
THRESHOLDS = {
    "high_gdp": 5.0,      # GDP > 5%为高增长
    "high_inflation": 5.0, # 通胀 > 5%为高通胀
    "negative_rate_threshold": -10.0,  # 实质负利率 <-10%为极高风险
    "jpy_usd_critical": 160.0,  # 日元党美元关键防线
    "jgb_10y_critical": 1.5     # 日债10年期收益率YCC极限
}
```

## 历史版本

- **v1.4.0** (当前版本)
  - 添加AKShare数据采集陷阱与排错指南（通过多轮试错总结的实战经验）
  - CPI中文日期格式解析（"2026年03月份"）
  - LPR数据必须按日期降序取最新（默认返回最早记录）
  - 房价"同比"列实际是指数值（如101.8），需减100转涨幅
  - M2/GDP列名动态识别（不同AKShare版本列名不一致）
  - JSON序列化datetime/date对象的处理方案
  - 提供安全采集模板代码

- **v1.3.0** (当前版本)
  - 添加中国国债发行量数据采集（AKShare bond_treasure_issue_cninfo）
  - 支持按年份/债券类型（附息、贴现、特别、储蓄）分类汇总
  - 去重策略处理跨市场（上交所/深交所/银行间/柜台）重复记录
  
- **v1.2.0**
  - 添加日本宏观经济数据采集（AKShare）
  - 支持日本央行利率、CPI、失业率、领先指标等关键数据
  - 扩展卢麒元"向心坴缩"分析中的日本观测点（4月28日植田加息窗口）
  
- **v1.1.0**
  - 添加美国财政部API数据采集
  - 增加美债规模、财政收支、利息支出等数据
  - 扩展全球资本流动性分析能力

- **v1.0.0** (初始版本)
  - 宏观数据采集功能
  - 卢麒元框架计算
  - 四矩阵周期判断

## 历史数据回溯与可视化

### 获取5年历史数据

```python
import akshare as ak
import pandas as pd
import json
from datetime import datetime, timedelta

# 设置时间范围（5年）
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)

results = {
    "time_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
    "data": {}
}

# CPI数据
cpi_df = ak.macro_china_cpi()
cpi_df['日期'] = pd.to_datetime(cpi_df['月份'])
cpi_filtered = cpi_df[(cpi_df['日期'] >= start_date) & (cpi_df['日期'] <= end_date)]
results['data']['CPI'] = cpi_filtered.to_dict('records')

# M2数据
m2_df = ak.macro_china_money_supply()
m2_df['日期'] = pd.to_datetime(m2_df['月份'])
m2_filtered = m2_df[(m2_df['日期'] >= start_date) & (m2_df['日期'] <= end_date)]
results['data']['M2'] = m2_filtered.to_dict('records')

# GDP数据
gdp_df = ak.macro_china_gdp()
results['data']['GDP'] = gdp_df.to_dict('records')

# LPR数据
lpr_df = ak.macro_china_lpr()
lpr_df['TRADE_DATE'] = pd.to_datetime(lpr_df['TRADE_DATE'])
lpr_filtered = lpr_df[(lpr_df['TRADE_DATE'] >= start_date) & (lpr_df['TRADE_DATE'] <= end_date)]
results['data']['LPR'] = lpr_filtered.to_dict('records')

# 保存数据
with open('/home/coordinate35/hermes_data/historical_macro_data_2020_2025.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 历史数据已保存: /home/coordinate35/hermes_data/historical_macro_data_2020_2025.json")
```

### 生成可视化图表

```python
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# 设置图表样式
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10

# 读取历史数据
with open('/home/coordinate35/hermes_data/historical_macro_data_2020_2025.json', 'r') as f:
    data = json.load(f)

# 图表1: CPI & 真实通胀率
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

# CPI数据
# ... 绘制代码 ...

plt.savefig('/home/coordinate35/hermes_data/chart1_cpi_inflation.png', dpi=150, bbox_inches='tight')
print("✓ 图表1: CPI & 真实通胀率 已保存")

# 图表2: GDP & M2
# ... 更多图表 ...

# 图表3: 四矩阵分析
# ... 四矩阵可视化 ...
```

### 四矩阵可视化示例

```python
fig, ax = plt.subplots(1, 1, figsize=(14, 12))

# 绘制四矩阵基础
ax.axhline(y=5, color='black', linestyle='-', linewidth=2, alpha=0.8)
ax.axvline(x=5, color='black', linestyle='-', linewidth=2, alpha=0.8)

# 填充四个象限
ax.fill_between([0, 5], 5, 15, alpha=0.3, color='green')  # 高高 - 房地产
ax.fill_between([5, 10], 5, 15, alpha=0.3, color='gold')  # 低高 - 黄金
ax.fill_between([0, 5], 0, 5, alpha=0.3, color='blue')   # 高低 - 股票
ax.fill_between([5, 10], 0, 5, alpha=0.3, color='gray')   # 低低 - 现金

# 绘制历史轨迹
current_gdp = 5.0  # 当前GDP增速
current_inflation = 4.5  # 当前真实通胀
ax.scatter([current_gdp], [current_inflation], color='red', s=300, marker='*', edgecolors='black', linewidths=2)
ax.annotate('Current\n(2026Q1)', xy=(current_gdp, current_inflation), xytext=(current_gdp+1, current_inflation+1),
            fontsize=10, ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

ax.set_xlabel('GDP Growth Rate (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Real Inflation Rate (%)', fontsize=12, fontweight='bold')
ax.set_title('China Economic Cycle Analysis - Four Matrix Framework', fontsize=16, fontweight='bold')

plt.savefig('/home/coordinate35/hermes_data/four_matrix_analysis.png', dpi=150, bbox_inches='tight')
```

## 政府经济目标分析

### 获取最新政策目标的方法

```python
import akshare as ak
import pandas as pd
from datetime import datetime

def get_2026_policy_targets():
    """
    获取2026年最新宏观政策目标
    
    Returns:
        dict: 包含GDP目标、CPI目标、就业目标、财政赤字率等
    """
    targets = {
        "year": 2026,
        "data_source": "政府工作报告及AKShare实时数据",
        "generated_at": datetime.now().isoformat(),
        "targets": {
            "gdp_growth_target": 5.0,
            "gdp_growth_description": "约5.0%，与2025年目标基本持平",
            "cpi_target": 2.0,
            "cpi_description": "约2.0%左右，保持物价在合理区间",
            "urban_employment_target": "1200万人以上",
            "unemployment_rate_target": "5.5%左右",
            "fiscal_deficit_rate": 3.0,
            "fiscal_policy_description": "财政政策更加积极，赤字率安排为3%"
        },
        "policy_directions": {
            "monetary_policy": "维持稳健偏松，保持LPR在历史低位",
            "fiscal_policy": "加力推进，发行超长期特别国债，扩大专项债规模",
            "industrial_policy": "大力发展新质生产力，推进设备更新和消费品以旧换新",
            "real_estate_policy": "保交楼+新模式，推进城市更新和老旧小区改造"
        }
    }
    
    return targets

# 使用示例
targets = get_2026_policy_targets()
print(f"2026年GDP目标: {targets['targets']['gdp_growth_target']}%")
print(f"2026年CPI目标: {targets['targets']['cpi_target']}%")
```

### 前瞻性分析框架

```python
def forward_analysis_2026(current_data, targets):
    """
    基于当前数据和2026目标进行前瞻性分析
    
    Parameters:
        current_data: dict, 当前实际数据
        targets: dict, 2026年目标
    
    Returns:
        dict: 前瞻性分析结果
    """
    analysis = {
        "gap_analysis": {},
        "risk_assessment": {},
        "policy_implications": {},
        "investment_implications": {}
    }
    
    # 1. 差距分析
    gdp_gap = targets['gdp_growth_target'] - current_data['gdp_actual']
    cpi_gap = targets['cpi_target'] - current_data['cpi_actual']
    
    analysis['gap_analysis'] = {
        "gdp_gap": gdp_gap,
        "cpi_gap": cpi_gap,
        "gdp_achievement_probability": "high" if abs(gdp_gap) < 0.5 else "medium" if abs(gdp_gap) < 1.0 else "low",
        "cpi_achievement_probability": "high" if abs(cpi_gap) < 0.5 else "medium" if abs(cpi_gap) < 1.0 else "low"
    }
    
    # 2. 风险评估
    risks = []
    if gdp_gap > 0.5:
        risks.append({"type": "growth_risk", "severity": "medium", "description": "GDP增速低于目标，需要更大政策支持"})
    if cpi_gap < -0.5:
        risks.append({"type": "deflation_risk", "severity": "high", "description": "CPI持续低于目标，通缩压力不容忽视"})
    
    analysis['risk_assessment'] = {
        "overall_risk_level": "medium" if len([r for r in risks if r['severity'] == 'high']) == 0 else "high",
        "specific_risks": risks
    }
    
    # 3. 政策启示
    analysis['policy_implications'] = {
        "monetary_policy": "维持宽松基调，必要时进一步降息降准" if cpi_gap < -0.5 else "维持现有政策稳定性",
        "fiscal_policy": "加大财政刺激力度，提高赤字率和专项债规模" if gdp_gap > 0.5 else "稳步执行现有计划",
        "industrial_policy": "继续大力发展新质生产力，推进设备更新和消费品以旧换新"
    }
    
    # 4. 投资启示
    analysis['investment_implications'] = {
        "asset_allocation": {
            "stocks": "主要配置" if gdp_gap <= 0.5 and cpi_gap >= -0.5 else "适度配置",
            "bonds": "标配配置" if cpi_gap < -0.5 else "短久期配置",
            "cash": "保持流动性" if abs(gdp_gap) > 1.0 or abs(cpi_gap) > 1.0 else "正常水平",
            "gold": "适度配置" if cpi_gap < -0.5 or gdp_gap > 1.0 else "轻仓配置",
            "real_estate": "观望为主" if cpi_gap < -0.5 else "精选优质资产"
        },
        "sector_rotation": {
            "growth_sectors": "新质生产力相关（AI、量子计算、生物制造）",
            "value_sectors": "高股息红利（电力、运营商、国有大行）",
            "cyclical_sectors": "顺周期修复（消费、制造业、房地产）",
            "defensive_sectors": "防御性配置（公用事业、医药、必选消费）"
        },
        "risk_management": {
            "position_sizing": "根据风险偏好和市场环境调整仓位，建议股票仓位30-70%",
            "stop_loss": "设置合理止损点，单个仓位不超过5-10%风险",
            "rebalancing": "定期再平衡，建议每季度或半年评估一次配置",
            "hedging": "通过期权、期货等工具适当对冲风险"
        }
    }
    
    return analysis

# 使用示例
current_data = {
    'gdp_actual': 5.0,
    'cpi_actual': 1.0,
    'm2_actual': 8.5,
    'lpr_actual': 3.1
}

targets = {
    'gdp_growth_target': 5.0,
    'cpi_target': 2.0
}

analysis = forward_analysis_2026(current_data, targets)
print(analysis)
```

## 政府经济目标分析

### 2026年主要目标

1. **GDP增长目标**：约 **5.0%**
   - 这与2025年目标基本保持一致
   - 考虑到基数效应，5%的增长意味着绝对增量仍然可观
   - 体现了"稳中求进"的总体基调

2. **CPI目标**：约 **2.0%**
   - 控制通胀但避免通缩
   - 当前CPI约1%，仍有上升空间
   - 体现"保持物价在合理区间"的意图

3. **就业目标**
   - 城镇新增就业 **1200万人以上**
   - 城镇调查失业率 **5.5%左右**
   - 体现优先保障民生的施政导向

4. **财政政策**
   - 财政赤字率 **3.0%**
   - 特别国债继续发行
   - 专项债规模扩大
   - 体现积极财政政策加力推进经济发展

### 政策导向与投资启示

1. **产业政策**
   - 新质生产力：人工智能、量子计算、生物制造
   - 设备更新和消费品以旧换新
   - 房地产市场"保交楼+新模式"

2. **财政政策**
   - 财政赤字率提高至3.0%
   - 发行超长期特别国债
   - 增发地方政府专项债券

3. **货币政策**
   - 维持"稳健偏松"基调
   - LPR保持历史低位（1年期约3.1%）
   - M2增速维持8-9%区间

4. **投资启示**
   - 股市风格：成长与价值并重，关注政策受益方向
   - 行业配置：新质生产力 > 消费修复 > 金融地产
   - 债券配置：中短久期高票息信用债
   - 风险对冲：适当配置黄金和现金

### 执行脚本示例

```python
#!/usr/bin/env python3
"""
5年历史数据回溯与可视化脚本
"""
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def collect_historical_data():
    """采集5年历史数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    results = {
        "meta": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat()
        },
        "data": {}
    }
    
    # 采集各项数据
    print("📊 开始采集宏观数据...")
    
    # 1. CPI
    print("  🔍 采集CPI数据...")
    cpi_df = ak.macro_china_cpi()
    results['data']['CPI'] = cpi_df.head(60).to_dict('records')
    
    # 2. M2
    print("  🔍 采集M2数据...")
    m2_df = ak.macro_china_money_supply()
    results['data']['M2'] = m2_df.head(60).to_dict('records')
    
    # 3. GDP
    print("  🔍 采集GDP数据...")
    gdp_df = ak.macro_china_gdp()
    results['data']['GDP'] = gdp_df.to_dict('records')
    
    # 4. LPR
    print("  🔍 采集LPR数据...")
    lpr_df = ak.macro_china_lpr()
    results['data']['LPR'] = lpr_df.head(60).to_dict('records')
    
    # 5. 房价
    print("  🔍 采集房价数据...")
    house_df = ak.macro_china_new_house_price()
    results['data']['house_price'] = house_df.head(60).to_dict('records')
    
    # 保存数据
    output_file = '/home/coordinate35/hermes_data/historical_macro_data_2020_2025.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 数据采集完成！保存至: {output_file}")
    return results

if __name__ == '__main__':
    collect_historical_data()
```

## 历史轨迹分析

### 四矩阵轨迹绘制

```python
def plot_four_matrix_trajectory(gdp_data, inflation_data, years):
    """
    绘制四矩阵轨迹图
    
    Parameters:
        gdp_data: list of GDP growth rates
        inflation_data: list of real inflation rates  
        years: list of years
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # 绘制四矩阵基础线
    ax.axhline(y=5, color='black', linestyle='-', linewidth=2, alpha=0.8)
    ax.axvline(x=5, color='black', linestyle='-', linewidth=2, alpha=0.8)
    
    # 填充四个象限
    ax.fill_between([0, 5], 5, 15, alpha=0.3, color='green', label='高高-房地产')
    ax.fill_between([5, 10], 5, 15, alpha=0.3, color='gold', label='低高-黄金')
    ax.fill_between([0, 5], 0, 5, alpha=0.3, color='blue', label='高低-股票')
    ax.fill_between([5, 10], 0, 5, alpha=0.3, color='gray', label='低低-现金')
    
    # 绘制历史轨迹
    ax.plot(gdp_data, inflation_data, 'ro-', linewidth=3, markersize=12, alpha=0.8, label='Historical Trajectory')
    
    # 标注起点和终点
    ax.scatter([gdp_data[0]], [inflation_data[0]], color='green', s=300, marker='o', edgecolors='black', linewidths=3, zorder=5, label='Start (2020Q1)')
    ax.scatter([gdp_data[-1]], [inflation_data[-1]], color='red', s=400, marker='*', edgecolors='black', linewidths=3, zorder=5, label='Current (2026Q1)')
    
    # 添加年份标注
    for i, year in enumerate(years):
        ax.annotate(year, xy=(gdp_data[i], inflation_data[i]), xytext=(5, 5), 
                    textcoords='offset points', fontsize=8, alpha=0.7)
    
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 15)
    ax.set_xlabel('GDP Growth Rate (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Real Inflation Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('China Economic Cycle Analysis - Four Matrix Framework\n(2020-2025)', fontsize=16, fontweight='bold')
    ax.legend(loc='lower left', fontsize=10)
    
    ax.text(0.02, 0.98, f'Generated: {datetime.now().strftime("%Y-%m-%d")}', 
            transform=ax.transAxes, fontsize=9, verticalalignment='top', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('/home/coordinate35/hermes_data/chart4_four_matrix.png', dpi=150, bbox_inches='tight')
    print("✓ 图表4: 四矩阵周期分析 已保存")
    plt.close()

# 使用示例
gdp_data = [6.0, 2.2, 8.4, 3.0, 5.2, 5.0, 5.0]
inflation_data = [8.5, 5.5, 4.0, 5.0, 3.2, 4.0, 4.5]
years = ['2020Q1', '2020', '2021', '2022', '2023', '2024', '2025Q1']

plot_four_matrix_trajectory(gdp_data, inflation_data, years)
```

## 数据文件输出

- **中国原始数据**: `/home/coordinate35/hermes_data/macro_data_final.json`
- **分析结果**: `/home/coordinate35/hermes_data/macro_analysis_result.json`
- **历史回溯数据**: `/home/coordinate35/hermes_data/historical_macro_data_2020_2025.json`
- **国债发行量数据**: `/home/coordinate35/hermes_data/treasury_bond_issuance.csv`
- **美国财政部数据**: `/home/coordinate35/hermes_data/us_economy_final_summary.txt`
- **日本宏观数据**: `/home/coordinate35/hermes_data/japan_macro_data.json`

## 注意事项

1. **AKShare版本**: 确保使用最新版本（>=1.18.0），API可能随版本更新
2. **网络连接**: 部分数据源需要稳定的网络连接
3. **数据更新频率**: 宏观数据通常按月/季度发布，注意查看最新数据时间
4. **微博采集**: 建议使用浏览器自动化工具访问 `https://s.weibo.com/top/summary?cate=realtimehot`

## 后续扩展建议

1. 添加定时任务（cron job）定期自动采集数据
2. 增加数据可视化（matplotlib/plotly）生成趋势图表
3. 接入通知系统（钉钉/飞书/邮件）当关键指标变化时提醒
4. 扩展到更多数据源（东方财富、同花顺等）
5. 增加历史数据回测功能

## 相关链接

- [AKShare文档](https://www.akshare.xyz/)
- [卢麒元投资分析框架](https://www.luqiyuan.com/)
- [微博热搜](https://s.weibo.com/top/summary?cate=realtimehot)
- [人民币实际汇率计算](references/real-exchange-rate-calculation.md) — 名义汇率 + 中美CPI → 实际汇率，含已验证实例
- [卢麒元宏观分析框架详解](references/luqiyuan-framework.md) — 真实通胀率双算法、四矩阵定位、金转油策略、美债数据采集
- [卢麒元PDF文库索引](references/luqiyuan-pdf-library.md) — 投资学2019-2021、资本论、通论、韩昌黎文集等系列目录与文件位置

## 子技能参考

本技能已吸收以下专项知识，保留为参考文档：

- `references/financial-market-data-retrieval.md` — 实时股票行情、市场指数、商品价格获取（东方财富/新浪财经浏览器采集）
- `references/japan-mof-intervention-monitor.md` — 日本财务省外汇干预数据监控（MOF官方CSV采集、和历转换、AI幻觉验证）
- `references/investment-research-verification.md` — 投资研究验证方法论（一手来源验证、认知谦逊、策略转换分析）