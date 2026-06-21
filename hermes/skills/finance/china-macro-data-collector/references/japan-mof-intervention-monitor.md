---
name: japan-mof-intervention-monitor
category: finance
description: |
  监控日本财务省(MOF)外汇干预操作数据的完整流程。
  包括：官方CSV数据采集、历史记录解析、AI幻觉验证、
  自动化监控与通知、与卢麒元投资分析框架的联动应用。
author: Assistant
tags: [japan, mof, fx-intervention, yen, csv, monitoring, luqiyuan]
version: 1.0.0
---

# 日本财务省外汇干预数据监控技能

## 背景

日元汇率是卢麒元投资分析框架中"向心坎缩"理论的核心观测点。日本政府的外汇干预操作（卖美元/买日元）是判断日元贬值是否触及"政府防线"的关键信号。

本技能提供从日本财务省官方CSV直接获取真实数据的完整方法，避免被AI生成的虚假报告误导。

## 数据源

### 主数据源（已验证可用）

| 数据源 | URL | 语言 | 编码 |
|:---|:---|:---|:---|
| 日文版CSV | `https://www.mof.go.jp/policy/international_policy/reference/feio/foreign_exchange_intervention_operations.csv` | 日文 | **cp932** |
| 英文版CSV | `https://www.mof.go.jp/english/policy/international_policy/reference/feio/foreign_exchange_intervention_operations.csv` | 英文 | utf-8 (但存在编码问题) |

**建议：始终使用日文版CSV**，用`cp932`编码解码，数据完整且更新及时。

### CSV字段结构

| 列 | 内容 | 说明 |
|:---:|:---|:---|
| 1 | 和历年号 | 令和/平成/昭和 |
| 2-3 | 月、日（和历） | 可为空（继承上行） |
| 4 | 公历年 | 可为空（继承上行） |
| 5-6 | 月、日（英文） | 可为空（继承上行） |
| 7 | 金额（亿日元） | 非零值表示实际干预 |
| 8 | 操作类型（日） | e.g. 米ドル売り・日本円買い |
| 9 | 操作类型（英） | e.g. the US dollar (sold) the Japanese yen (bought) |

**关键特点：CSV使用"继承"格式** — 同一和历年的后续行，年月日字段为空，需要向下继承上一行的值。

## 核心技术流程

### 1. 数据下载与解析

```python
import urllib.request
import ssl
import csv
import re

# MOF官网需要关闭SSL校验
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://www.mof.go.jp/policy/international_policy/reference/feio/foreign_exchange_intervention_operations.csv"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
    # **关键：使用cp932编码**
    data = resp.read().decode("cp932", errors="ignore")
```

### 2. 和历→公历转换

```python
def era_to_gregorian(era_name: str, era_num: int) -> int:
    """和历年号转换为公历年份"""
    if era_name == "令和":
        return 2018 + era_num
    elif era_name == "平成":
        return 1988 + era_num
    elif era_name == "昭和":
        return 1925 + era_num
    return 0
```

### 3. 干预记录解析（含继承逻辑）

```python
def parse_interventions(csv_content: str) -> list[dict]:
    """解析CSV，提取所有非零干预记录"""
    lines = csv_content.strip().split("\n")
    reader = csv.reader(lines)
    rows = list(reader)

    interventions = []
    current_era = ""
    current_year = ""

    for row in rows[1:]:
        if len(row) < 9:
            continue

        # 更新年号（如果当前行有）
        if row[0].strip() and "年" in row[0]:
            current_era = row[0].strip()
            era_match = re.search(r"(令和|平成|昭和)(\d+)年", current_era)
            if era_match:
                current_year = str(era_to_gregorian(
                    era_match.group(1), 
                    int(era_match.group(2))
                ))

        # 公历年字段可能覆盖
        if row[3].strip() and row[3].strip().isdigit():
            current_year = row[3].strip()

        # 提取金额（排除季度合计行）
        amount_str = row[6].strip().replace('"', "").replace(",", "")
        if amount_str and amount_str != "0" and "期計" not in row[0]:
            amount = int(amount_str)
            direction = "阻止日元贬值" if "日本円買い" in row[7] else "阻止日元升值"
            interventions.append({
                "year": int(current_year) if current_year else 0,
                "month": row[4],
                "day": row[5],
                "amount_billion_yen": amount,
                "amount_trillion_yen": round(amount / 10000, 4),
                "operation_jp": row[7],
                "direction": direction,
            })

    return interventions
```

### 4. 哈希检测更新

```python
import hashlib

def compute_hash(content: str) -> str:
    return hashlib.md5(content.encode("utf-8")).hexdigest()

# 保存上次哈希，每次运行时比对
# 变化才解析，减少计算量
```

## 典型数据与验证

### 历史干预记录汇总

| 时期 | 年份 | 次数 | 合计金额 | 方向 |
|:---|:---|:---:|:---|:---|
| 令和4年 | 2022 | 3次 | 9.19万亿日元 | 阻止贬值 |
| 令和6年 | 2024 | 4次 | 15.32万亿日元 | 阻止贬值 |
| 平成23年 | 2011 | 7次 | 14.30万亿日元 | 阻止升值 |
| 平成15-16年 | 2003-04 | 138次 | 35.26万亿日元 | 阻止升值 |

### 最大单笔干预 TOP 5

| 排名 | 日期 | 金额 | 方向 |
|:---:|:---|:---|:---|
| 1 | 2011/10/31 | **8.07万亿日元** | 阻止升值 |
| 2 | 2024/4/29 | **5.92万亿日元** | 阻止贬值 |
| 3 | 2022/10/21 | **5.62万亿日元** | 阻止贬值 |
| 4 | 2011/8/4 | **4.51万亿日元** | 阻止升值 |
| 5 | 2024/5/1 | **3.87万亿日元** | 阻止贬值 |

## AI幻觉验证方法

当遇到关于日本外汇干预的第三方报告时，按以下步骤验证：

### 验证清单

1. **检查大臣姓名**
   - 财务大臣是否为"加藤胜信"（或当时现任）
   - 片山さつき曾任地方创生担当大臣，非财务大臣

2. **检查日期**
   - 对照CSV中是否存在该日期的记录
   - 官方数据通常比实际干预晚1-2个月公布

3. **检查金额**
   - 5.48万亿→官方记录中不存在
   - 最接近的是2024年7月11-12日合计5.53万亿

4. **检查操作类型**
   - 近年日本只做"卖美元/买日元"（阻止贬值）
   - 如果报告说"买美元/卖日元"需要确认是否为历史记录

## 与卢麒元框架的联动

### 向心坎缩观测点

| 观测点 | 阈值/信号 | 判断 |
|:---|:---|:---|
| **日元党美元汇率** | 突破 160 | 日央行信誉防线失守，套息交易平仓触发 |
| **日债10年期收益率** | 突破 1.5% | YCC控制极限，日债流动性危机 |
| **日本核心CPI** | 持续 > 2.5% 或 < 1.0% | >2.5%加息压力/<1.0%通缩压力 |
| **BOJ政策利率** | 每次加息25bp | 资本流向迅速改变 |
| **外汇干预规模** | 单次 > 3万亿日元 | 政府"真金白银"入市，信号强烈 |

### 传导链条

```
日元加息 → 日债收益率飙升 → 日债价格暴跌 → 日本金融机构浮亏 
  → 海外资产（美债/美股）被迫回流 → 全球流动性缩紧 → 速冻 → 向心坎缩
```

### 四矩阵定位

日本当前处于 **低增长 + 输入型高通胀** → "低高"矩阵 → 黄金为避险首选

## 自动化部署脚本

### 完整监控脚本示例

见 `/home/coordinate35/hermes_data/japan_mof_intervention_monitor.py`

### 定时任务设置

```bash
# 每天上午9:00自动执行
cronjob create "日本财务省外汇干预监控" \
  --schedule "0 9 * * *" \
  --command "cd /home/coordinate35/hermes_data && python3 japan_mof_intervention_monitor.py"
```

## 常见问题与解决

### 问题1: 网络访问超时

**解决**: 增加timeout至30秒，使用SSL上下文关闭验证

```python
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
    ...
```

### 问题2: 乱码/编码错误

**解决**: 日本政府网站通常使用`cp932`而非`utf-8`

```python
data = resp.read().decode("cp932", errors="ignore")
```

### 问题3: 日期解析错误

**解决**: CSV中同一年号的后续行字段为空，需要向下继承

```python
# 继承逻辑
if row[0].strip() and "年" in row[0]:
    current_era = row[0].strip()
    # 更新current_year
```

### 问题4: 季度合计行混入

**解决**: 排除含"期計"的行

```python
if "期計" not in row[0] and "期計" not in row[2]:
    # 处理该行
```

## 数据文件输出

| 文件 | 内容 |
|:---|:---|
| `intervention_history.json` | 完整历史干预记录 |
| `latest_intervention.json` | 最新数据摘要 |
| `last_hash.txt` | 文件MD5哈希 |
| `report_YYYYMMDD_HHMMSS.txt` | 每次检测报告 |
| `monitor.log` | 运行日志 |

## 扩展建议

1. **结合美债数据**: 日本持有约$1.1万亿美债，干预规模与美债回流存在联动
2. **结合汇率数据**: 同步获取USD/JPY实时汇率，计算干预"效果"
3. **结合BOJ政策**: 监控BOZ利率决议，预判干预需求
4. **图表可视化**: 使用matplotlib生成干预规模时序图

## 相关链接

- [MOF外汇干预操作页面](https://www.mof.go.jp/policy/international_policy/reference/feio/index.html)
- [AKShare日本宏观数据](https://www.akshare.xyz/)
- [LU麒元投资框架](https://www.luqiyuan.com/)