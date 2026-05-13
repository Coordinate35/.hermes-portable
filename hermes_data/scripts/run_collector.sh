#!/bin/bash
# 中国宏观经济数据采集启动脚本
# 使用方式: ./run_collector.sh
# 路径: /home/coordinate35/hermes_data/scripts/

set -e  # 遇到错误立即退出

# 配置
BASE_DIR="/home/coordinate35/hermes_data"
VENV_DIR="$BASE_DIR/venv/.venv"
SCRIPT_PATH="$BASE_DIR/scripts/macro_collector.py"
DATA_DIR="$BASE_DIR/data"
LOGS_DIR="$BASE_DIR/logs"

# 创建必要目录
mkdir -p "$DATA_DIR" "$LOGS_DIR"

# 日志文件
LOG_FILE="$LOGS_DIR/collector_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 启动中国宏观经济数据采集..."
echo "=================================================="
echo "📁 工作目录: $BASE_DIR"
echo "📝 日志文件: $LOG_FILE"
echo "=================================================="
echo ""

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 错误: 虚拟环境不存在!"
    echo "请先运行初始化脚本..."
    exit 1
fi

# 检查Python脚本
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 采集脚本不存在!"
    echo "路径: $SCRIPT_PATH"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source "$VENV_DIR/bin/activate"
echo "✅ 虚拟环境已激活"
echo ""

# 检查依赖
echo "🔍 检查依赖..."
python3 << 'PYEOF'
import sys

try:
    import akshare
    import pandas
    print("✅ akshare 已安装")
    print(f"   版本: {akshare.__version__}")
    print("✅ pandas 已安装")
    print(f"   版本: {pandas.__version__}")
except ImportError as e:
    print(f"❌ 依赖缺失: {e}")
    print("正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "akshare", "pandas"])
    print("✅ 依赖安装完成")
PYEOF

echo ""
echo "🚀 开始运行数据采集脚本..."
echo "=================================================="
echo ""

# 运行主脚本
python3 "$SCRIPT_PATH" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=================================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 数据采集完成！"
    echo "📁 数据保存位置:"
    echo "   - 原始数据: $DATA_DIR/macro_data.json"
    echo "   - 分析结果: $DATA_DIR/macro_analysis.json"
    echo "📝 日志文件: $LOG_FILE"
else
    echo "❌ 数据采集失败!"
    echo "请查看日志: $LOG_FILE"
    exit 1
fi

echo "=================================================="
echo "🎉 任务完成！"
echo "=================================================="
