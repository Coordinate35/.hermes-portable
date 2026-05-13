# 美国财政部官方API速查卡

## 基础URL
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service
```

## 核心数据端点

### 1. 国债总额 (每日更新)
- **端点**: `/v2/accounting/od/debt_to_penny`
- **描述**: 国债总额及构成
- **关键字段**:
  - `record_date` - 日期
  - `tot_pub_debt_out_amt` - 国债总额
  - `debt_held_public_amt` - 公众持有
  - `intragov_hold_amt` - 政府间持有
- **最新数据(2026-04-20)**: $38.99万亿

### 2. 财政收支概览 (每月更新)
- **端点**: `/v1/accounting/mts/mts_table_1`
- **描述**: 收入、支出、赤字/盈余概览
- **关键字段**:
  - `current_month_gross_rcpt_amt` - 当月收入
  - `current_month_gross_outly_amt` - 当月支出
  - `current_month_dfct_sur_amt` - 当月赤字/盈余
- **最新数据(2026-03)**: 收入$327B, 支出$584B, 赤字$257B

### 3. 财政收入明细 (每月更新)
- **端点**: `/v1/accounting/mts/mts_table_2`
- **描述**: 税收和其他收入明细分类
- **关键字段**:
  - `classification_desc` - 收入类别
  - `current_month_rcpt_outly_amt` - 当月金额

### 4. 财政支出明细 (每月更新)
- **端点**: `/v1/accounting/mts/mts_table_3`
- **描述**: 政府部门支出明细分类
- **关键字段**:
  - `classification_desc` - 支出类别
  - `current_month_rcpt_outly_amt` - 当月金额

### 5. 国债利息支出 (每月更新)
- **端点**: `/v2/accounting/od/interest_expense`
- **描述**: 国债利息支出明细
- **关键字段**:
  - `record_date` - 日期
  - `interest_expense_amt` - 利息支出金额

### 6. 国债余额历史 (每季更新)
- **端点**: `/v2/accounting/od/debt_outstanding`
- **描述**: 国债余额历史数据(季度)
- **关键字段**:
  - `record_date` - 日期
  - `debt_outstanding_amt` - 债务余额

## Python调用示例

```python
import requests
import pandas as pd

# 基础URL
base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# 获取国债总额
def get_us_debt():
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

# 获取财政收支数据
def get_fiscal_data():
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

fiscal_df = get_fiscal_data()
print(f"财政数据记录数: {len(fiscal_df)}")
```

## 关键数据速查

| 指标 | 最新值 | 日期 |
|:---:|:---:|:---:|
| 国债总额 | $38.99万亿 | 2026-04-20 |
| 公众持有 | $31.34T (80.4%) | 2026-04-20 |
| 政府间持有 | $7.65T (19.6%) | 2026-04-20 |
| 日均增长 | ~$60亿 | 535天平均 |
| 当月收入 | $327B | 2026-03 |
| 当月支出 | $584B | 2026-03 |
| 当月赤字 | $257B | 2026-03 |

---

**保存日期**: 2026-04-22
**数据来源**: 美国财政部官方API (api.fiscaldata.treasury.gov)
