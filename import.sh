#!/usr/bin/env bash
set -euo pipefail

#
# Hermes Agent 完整恢复脚本
# 从 GitHub clone 的备份 → 新机器
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST_HERMES="${1:-${HOME}/.hermes}"
DST_DATA="${2:-${HOME}/hermes_data}"

echo "=== Hermes Portable Import ==="
echo "[*] 备份目录: $SCRIPT_DIR"
echo "[*] Hermes 目标: $DST_HERMES"
echo "[*] Data 目标: $DST_DATA"

# ---------------------------------------------------------------------------
# 0. 检查必需条件
# ---------------------------------------------------------------------------
if [[ ! -d "$SCRIPT_DIR/hermes" ]]; then
    echo "[!] 错误: 在 $SCRIPT_DIR 下未找到 hermes/ 目录"
    echo "    请确保你在正确的备份目录中运行此脚本。"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. 恢复 ~/.hermes 配置
# ---------------------------------------------------------------------------
echo "[*] 恢复 Hermes 配置..."
mkdir -p "$DST_HERMES"

# SOUL.md
if [[ -f "$SCRIPT_DIR/hermes/SOUL.md" ]]; then
    cp "$SCRIPT_DIR/hermes/SOUL.md" "$DST_HERMES/"
    echo "    SOUL.md ✓"
fi

# memories/
if [[ -d "$SCRIPT_DIR/hermes/memories" ]]; then
    mkdir -p "$DST_HERMES/memories"
    rsync -a --delete "$SCRIPT_DIR/hermes/memories/" "$DST_HERMES/memories/"
    echo "    memories/ ✓"
fi

# skills/
if [[ -d "$SCRIPT_DIR/hermes/skills" ]]; then
    mkdir -p "$DST_HERMES/skills"
    rsync -a --delete "$SCRIPT_DIR/hermes/skills/" "$DST_HERMES/skills/"
    echo "    skills/ ✓"
fi

# cron/jobs.json
if [[ -f "$SCRIPT_DIR/hermes/cron/jobs.json" ]]; then
    mkdir -p "$DST_HERMES/cron"
    cp "$SCRIPT_DIR/hermes/cron/jobs.json" "$DST_HERMES/cron/"
    echo "    cron/jobs.json ✓"
fi

# scripts/
if [[ -d "$SCRIPT_DIR/hermes/scripts" ]]; then
    mkdir -p "$DST_HERMES/scripts"
    rsync -a --delete "$SCRIPT_DIR/hermes/scripts/" "$DST_HERMES/scripts/"
    echo "    scripts/ ✓"
fi

# config.yaml（需要用户手动填入 API Key）
if [[ -f "$SCRIPT_DIR/hermes/config.yaml" ]]; then
    cp "$SCRIPT_DIR/hermes/config.yaml" "$DST_HERMES/config.yaml"
    echo "    config.yaml ✓ (请稍后填入 API Key)"
fi

# ---------------------------------------------------------------------------
# 2. 恢复全息记忆数据库
# ---------------------------------------------------------------------------
SQL_FILE="$SCRIPT_DIR/hermes/memory_store_core.sql"
if [[ -f "$SQL_FILE" ]]; then
    echo "[*] 恢复全息记忆数据库..."

    # 删除旧数据库（如果存在）
    rm -f "$DST_HERMES/memory_store.db"

    # 使用 Python 的 sqlite3 导入（更稳定，不依赖 sqlite3 CLI）
    python3 -c "
import sqlite3, os
sql_path = '$SQL_FILE'
db_path = '$DST_HERMES/memory_store.db'

# 创建新数据库
conn = sqlite3.connect(db_path)

# 读取 SQL 并执行
with open(sql_path, 'r') as f:
    sql_script = f.read()

conn.executescript(sql_script)
conn.commit()
conn.close()
print(f'    导入完成: {db_path}')
"
    echo "    全息记忆文本数据 ✓"

    # -----------------------------------------------------------------------
    # 3. 重建 HRR 向量
    # -----------------------------------------------------------------------
    echo "[*] 正在重建 HRR 向量..."
    if [[ -f "$SCRIPT_DIR/scripts/rebuild_vectors.py" ]]; then
        python3 "$SCRIPT_DIR/scripts/rebuild_vectors.py"
    else
        echo "    [!] 未找到 rebuild_vectors.py，跳过向量重建"
        echo "        警告：全息记忆将无法正常工作！"
    fi
else
    echo "    [i] 未找到 memory_store_core.sql，跳过全息记忆恢复"
fi

# ---------------------------------------------------------------------------
# 4. 恢复 ~/hermes_data
# ---------------------------------------------------------------------------
if [[ -d "$SCRIPT_DIR/hermes_data" ]]; then
    echo "[*] 恢复 hermes_data..."
    mkdir -p "$DST_DATA"
    rsync -a --delete "$SCRIPT_DIR/hermes_data/" "$DST_DATA/"
    echo "    hermes_data/ ✓"
fi

# ---------------------------------------------------------------------------
# 5. 其他说明
# ---------------------------------------------------------------------------
echo ""
echo "=== 恢复完成 ==="
echo ""
echo "接下来请完成以下步骤："
echo ""
echo "1. 填入 API Key"
echo "   编辑: $DST_HERMES/config.yaml"
echo "   将所有 __REPLACE_WITH_YOUR_KEY__ 替换为真实的 API Key"
echo ""

# 检查是否需要填入 .env
if [[ -f "$DST_HERMES/.env" ]]; then
    echo "2. 检查 .env 文件: $DST_HERMES/.env"
else
    echo "2. 如需 .env 环境变量，请手动创建 $DST_HERMES/.env"
fi

echo ""
echo "3. 安装 Hermes Agent 依赖（如果尚未安装）"
echo "   例如: pip install -r hermes-agent/requirements.txt"
echo ""
echo "4. 启动 Hermes Agent"
echo ""
echo "注意："
echo "- state.db 未恢复（会话历史从头开始，这是正常的）"
echo "- 如果 hermes_data 中包含 venv/，请重新创建虚拟环境"
echo ""
