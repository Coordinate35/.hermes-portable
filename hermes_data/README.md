# 📊 Hermes 宏观经济数据采集系统

## 🏠 工作目录

所有数据、脚本和配置都集中存放在：

```
/home/coordinate35/hermes_data/
```

## 📁 目录结构

```
hermes_data/
├── README.md                 # 本文件
├── scripts/                  # 采集脚本目录
│   ├── macro_collector.py   # 核心采集脚本
│   └── run_collector.sh     # 便捷启动脚本
├── data/                     # 数据文件目录
│   ├── macro_data.json      # 原始采集数据
│   ├── macro_analysis.json  # 分析结果
│   └── weibo_hot_*.json     # 微博热搜数据
├── venv/                     # Python虚拟环境
│   └── .venv/               # 虚拟环境目录
├── config/                   # 配置文件目录
│   └── keywords.json        # 微博关键词配置
└── logs/                     # 日志文件目录
    └── collector_*.log      # 采集日志
```

## 🚀 快速开始

### 方式1：使用便捷脚本（推荐）

```bash
# 直接运行启动脚本
/home/coordinate35/hermes_data/scripts/run_collector.sh
```

### 方式2：直接运行Python脚本

```bash
cd /home/coordinate35/hermes_data
source venv/.venv/bin/activate
python scripts/macro_collector.py
```

### 方式3：让AI助手帮你运行

> 对我说：**"运行宏观经济数据采集"**

我会立即为你采集最新数据！

## 📊 采集内容

### 宏观经济指标

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| CPI同比 | 消费者物价指数同比涨幅 | AKShare |
| M2同比增速 | 广义货币供应量同比增速 | AKShare |
| GDP同比增速 | 国内生产总值同比增速 | AKShare |
| 5年期LPR | 贷款市场报价利率（5年期） | AKShare |
| 房价同比涨幅 | 70城新建商品住房价格指数 | AKShare |
| 股市涨幅 | 上证指数区间涨跌幅 | AKShare |

### 卢麒元投资分析框架

1. **真实通胀率计算**
   - 公式1（货币供应量法）：`真实通胀 = CPI + (M2增速 - GDP增速)`
   - 公式2（资产配置法）：`真实通胀 = 60%×CPI + 20%×房价涨幅 + 20%×股市涨幅`

2. **实质利率计算**
   - `实质利率 = 名义利率 - 真实通胀率`

3. **四矩阵周期判断**
   | 状态 | 经济增长 | 通胀水平 | 投资策略 |
   |:---:|:---:|:---:|:---:|
   | **高高** | 高增长 | 高通胀 | 🏠房地产 |
   | **低高** | 低增长 | 高通胀 | 🥇黄金 |
   | **高低** | 高增长 | 低通胀 | 📈股票/实体经济 |
   | **低低** | 低增长 | 低通胀 | 💰现金/债券 |

4. **止损券分析**
   - 根据实质负利率判断风险等级和操作指导

## 📁 输出文件

运行后会生成以下文件：

```
data/
├── macro_data.json          # 原始采集数据
├── macro_analysis.json      # 分析结果（包含四矩阵判断和投资建议）
└── weibo_hot_YYYYMMDD_HHMMSS.json  # 微博热搜数据（如采集了微博）
```

## ⚙️ 配置说明

### 修改采集参数

编辑脚本文件：`scripts/macro_collector.py`

关键配置项在文件开头的 **配置** 区域：

```python
# 阈值配置
GDP_GROWTH_THRESHOLD = 5.0  # GDP增速阈值（判断高/低增长）
INFLATION_THRESHOLD = 5.0   # 通胀阈值（判断高/低通胀）

# 输出路径
OUTPUT_DIR = "/home/coordinate35/hermes_data"
```

### 添加微博关键词

编辑文件：`config/keywords.json`

```json
{
  "中东": ["沙特", "伊朗", "以色列", ...],
  "经济金融": ["股市", "汇率", "通胀", ...],
  "政策": ["发改委", "国务院", "财政部", ...]
}
```

## 🔧 维护说明

### 更新依赖

```bash
cd /home/coordinate35/hermes_data
source venv/.venv/bin/activate
pip install --upgrade akshare pandas
```

### 检查数据更新

宏观数据通常按月/季度发布，建议：
- **月度数据**（CPI、M2、LPR）：每月更新
- **季度数据**（GDP）：每季度更新
- **年度数据**：每年更新

### 日志查看

```bash
# 查看最新日志
ls -lt /home/coordinate35/hermes_data/logs/ | head

# 查看具体日志内容
cat /home/coordinate35/hermes_data/logs/collector_YYYYMMDD_HHMMSS.log
```

## 🆘 常见问题

### Q1: 提示"akshare未安装"

**解决**：
```bash
cd /home/coordinate35/hermes_data
source venv/.venv/bin/activate
pip install akshare pandas
```

### Q2: 数据采集失败/超时

**可能原因**：
- 网络连接问题
- AKShare API暂时不可用
- 数据发布时间未到

**解决**：
- 检查网络连接
- 稍后重试
- 查看AKShare官方文档

### Q3: 如何修改输出路径？

**解决**：
编辑 `scripts/macro_collector.py`，修改开头的：
```python
OUTPUT_DIR = "/your/custom/path"
```

## 📞 获取帮助

如有问题：
1. 查看本README文档
2. 检查日志文件
3. 访问 [AKShare文档](https://www.akshare.xyz/)
4. 询问AI助手

---

**最后更新**: 2026-04-21  
**版本**: 1.0.0  
**作者**: Assistant
