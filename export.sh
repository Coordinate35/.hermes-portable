#!/usr/bin/env bash
set -euo pipefail

#
# Hermes Agent 完整导出脚本
# 将 ~/.hermes 配置 + ~/hermes_data 用户数据 → 备份到 GitHub
#

SRC_HERMES="${HOME}/.hermes"
SRC_DATA="${HOME}/hermes_data"
DST="${HOME}/.hermes-portable"

# ---------------------------------------------------------------------------
# 检查必需路径
# ---------------------------------------------------------------------------
if [[ ! -d "$SRC_HERMES" ]]; then
    echo "[!] 源目录不存在: $SRC_HERMES"
    exit 1
fi

echo "=== Hermes Portable Export ==="
echo "[*] 源: $SRC_HERMES"
echo "[*] 目标: $DST"

# ---------------------------------------------------------------------------
# 1. 备份 ~/.hermes 关键配置
# ---------------------------------------------------------------------------
echo "[*] 备份 Hermes 配置..."

# SOUL.md
if [[ -f "$SRC_HERMES/SOUL.md" ]]; then
    cp "$SRC_HERMES/SOUL.md" "$DST/hermes/"
    echo "    SOUL.md ✓"
fi

# memories/
if [[ -d "$SRC_HERMES/memories" ]]; then
    mkdir -p "$DST/hermes/memories"
    rsync -a --delete --exclude='*.lock' "$SRC_HERMES/memories/" "$DST/hermes/memories/"
    echo "    memories/ ✓"
fi

# skills/
if [[ -d "$SRC_HERMES/skills" ]]; then
    mkdir -p "$DST/hermes/skills"
    rsync -a --delete \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.DS_Store' \
        "$SRC_HERMES/skills/" "$DST/hermes/skills/"
    echo "    skills/ ✓"
fi

# cron/jobs.json
if [[ -f "$SRC_HERMES/cron/jobs.json" ]]; then
    mkdir -p "$DST/hermes/cron"
    cp "$SRC_HERMES/cron/jobs.json" "$DST/hermes/cron/"
    echo "    cron/jobs.json ✓"
fi

# scripts/
if [[ -d "$SRC_HERMES/scripts" ]]; then
    mkdir -p "$DST/hermes/scripts"
    rsync -a --delete \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.log' \
        "$SRC_HERMES/scripts/" "$DST/hermes/scripts/"
    echo "    scripts/ ✓"
fi

# ---------------------------------------------------------------------------
# 2. 脱敏并备份 config.yaml
# ---------------------------------------------------------------------------
echo "[*] 备份配置（自动脱敏 API Key）..."
if [[ -f "$SRC_HERMES/config.yaml" ]]; then
    python3 -c "
import re, os

src = os.path.expanduser('$SRC_HERMES/config.yaml')
dst = os.path.expanduser('$DST/hermes/config.yaml')

with open(src, 'r') as f:
    raw = f.read()

# 替换各种 api_key 形式
redacted = re.sub(r'^(\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', raw, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*-\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', redacted, flags=re.MULTILINE)

# 替换其他敏感字段（可选）
redacted = re.sub(r'^(\s*api_secret:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_SECRET__', redacted, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*token:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_TOKEN__', redacted, flags=re.MULTILINE)

with open(dst, 'w') as f:
    f.write('# WARNING: Secrets redacted. Fill placeholders before use.\n')
    f.write(redacted)
"
    echo "    config.yaml ✓ (已脱敏)"
fi

# ---------------------------------------------------------------------------
# 3. 导出全息记忆数据库（排除 hrr_vector / memory_banks.vector BLOB）
# ---------------------------------------------------------------------------
MEMORY_DB="$SRC_HERMES/memory_store.db"
if [[ -f "$MEMORY_DB" ]]; then
    echo "[*] 导出全息记忆数据库（文本导出，无 BLOB 向量）..."

    python3 -c "
import sqlite3, os, sys

db_path = os.path.expanduser('$MEMORY_DB')
dst_path = os.path.expanduser('$DST/hermes/memory_store_core.sql')

if not os.path.exists(db_path):
    print('    [!] 数据库不存在，跳过')
    sys.exit(0)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 检查 facts 数量
cursor.execute('SELECT COUNT(*) FROM facts')
fact_count = cursor.fetchone()[0]

# 检查表是否存在
def table_exists(name):
    cursor.execute(\"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?\", (name,))
    return cursor.fetchone() is not None

skip_tables = {'facts_fts', 'facts_fts_config', 'facts_fts_data',
               'facts_fts_docsize', 'facts_fts_idx', 'sqlite_sequence'}

with open(dst_path, 'w') as f:
    f.write('-- Hermes Holographic Memory Export (text-only)\n')
    f.write(f'-- Facts count: {fact_count}\n')
    f.write(f'-- Exported: ' + __import__('datetime').datetime.now().isoformat() + '\n')
    f.write('BEGIN TRANSACTION;\n\n')

    # 1. Schema（保留完整表结构，包括 hrr_vector BLOB 列）
    for name, sql in cursor.execute(
        \"SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name\"
    ):
        if name in skip_tables or not sql:
            continue
        f.write(f'{sql};\n')
    f.write('\n')

    # 2. facts — 只插入文本列（跳过 hrr_vector BLOB）
    if table_exists('facts'):
        cursor.execute('''
            SELECT fact_id, content, category, tags, trust_score,
                   retrieval_count, helpful_count, created_at, updated_at
            FROM facts ORDER BY fact_id
        ''')
        for row in cursor.fetchall():
            vals = []
            for v in row:
                if v is None:
                    vals.append('NULL')
                elif isinstance(v, str):
                    vals.append(repr(v))
                else:
                    vals.append(str(v))
            f.write('INSERT INTO facts(fact_id, content, category, tags, trust_score, ' +
                    'retrieval_count, helpful_count, created_at, updated_at) ' +
                    'VALUES(' + ','.join(vals) + ');\n')
        f.write('\n')

    # 3. entities
    if table_exists('entities'):
        cursor.execute('PRAGMA table_info(entities)')
        entity_cols = [c[1] for c in cursor.fetchall()]
        col_str = ','.join(entity_cols)
        for row in cursor.execute(f'SELECT * FROM entities ORDER BY entity_id'):
            vals = []
            for v in row:
                if v is None:
                    vals.append('NULL')
                elif isinstance(v, str):
                    vals.append(repr(v))
                else:
                    vals.append(str(v))
            f.write('INSERT INTO entities(' + col_str + ') VALUES(' + ','.join(vals) + ');\n')
        f.write('\n')

    # 4. fact_entities
    if table_exists('fact_entities'):
        for row in cursor.execute('SELECT * FROM fact_entities ORDER BY rowid'):
            vals = []
            for v in row:
                if v is None:
                    vals.append('NULL')
                elif isinstance(v, str):
                    vals.append(repr(v))
                else:
                    vals.append(str(v))
            f.write('INSERT INTO fact_entities VALUES(' + ','.join(vals) + ');\n')
        f.write('\n')

    # 5. memory_banks — 只插入文本列（跳过 vector BLOB）
    if table_exists('memory_banks'):
        for row in cursor.execute(
            'SELECT bank_id, bank_name, dim, fact_count, updated_at FROM memory_banks ORDER BY bank_id'
        ):
            vals = []
            for v in row:
                if v is None:
                    vals.append('NULL')
                elif isinstance(v, str):
                    vals.append(repr(v))
                else:
                    vals.append(str(v))
            f.write('INSERT INTO memory_banks(bank_id, bank_name, dim, fact_count, updated_at) ' +
                    'VALUES(' + ','.join(vals) + ');\n')
        f.write('\n')

    # 6. Indexes
    for (sql,) in cursor.execute(\"SELECT sql FROM sqlite_master WHERE type='index' ORDER BY name\"):
        if sql and not any(s in sql for s in skip_tables):
            f.write(f'{sql};\n')
    f.write('\n')

    f.write('COMMIT;\n')

conn.close()
print(f'    memory_store_core.sql ✓ ({fact_count} facts)')
"
else
    echo "    [!] 未找到 memory_store.db，跳过全息记忆导出"
fi

# ---------------------------------------------------------------------------
# 4. 备份 ~/hermes_data
# ---------------------------------------------------------------------------
if [[ -d "$SRC_DATA" ]]; then
    echo "[*] 备份 hermes_data..."
    mkdir -p "$DST/hermes_data"
    rsync -a --delete \
        --exclude='venv' \
        --exclude='.venv' \
        --exclude='env' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='logs' \
        --exclude='*.log' \
        --exclude='*.db' \
        --exclude='*.db-wal' \
        --exclude='*.db-shm' \
        --exclude='.DS_Store' \
        --exclude='*.tmp' \
        --exclude='*.temp' \
        --exclude='*.bak' \
        --exclude='*.backup' \
        --exclude='cache' \
        --exclude='node_modules' \
        --exclude='*.key' \
        --exclude='*.pem' \
        --exclude='*.onnx' \
        --exclude='secrets/' \
        "$SRC_DATA/" "$DST/hermes_data/"
    echo "    hermes_data/ ✓"

    # 安全检查：确保密钥文件未被复制到备份目录
    if find "$DST/hermes_data" -name "*.key" -o -name "*.pem" | grep -q .; then
        echo "    [!!] 警告：备份中检测到密钥文件，正在删除..."
        find "$DST/hermes_data" \( -name "*.key" -o -name "*.pem" \) -delete
    fi
else
    echo "[!] 未找到 $SRC_DATA，跳过"
fi

# ---------------------------------------------------------------------------
# 5. 复制独立脚本
# ---------------------------------------------------------------------------
cp "$DST/scripts/rebuild_vectors.py" "$DST/scripts/rebuild_vectors.py" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 6. Git 提交并推送
# ---------------------------------------------------------------------------
echo "[*] Git 提交..."
cd "$DST"

# 添加所有文件
git add -A

# 检查是否有变更
if git diff --cached --quiet; then
    echo "[i] 无变更，跳过提交"
else
    git commit -m "sync: $(date +%Y-%m-%d-%H:%M)" || true
    echo "    Git 提交 ✓"

    # 尝试推送
    if git remote get-url origin >/dev/null 2>&1; then
        echo "[*] 推送到远程..."
        if git push origin main; then
            echo "    Git 推送 ✓"
        else
            echo "    [!] 推送失败，请检查网络或认证"
        fi
    else
        echo "[!] 未配置远程仓库，跳过推送"
        echo "    提示: git remote add origin https://github.com/YOUR_USER/hermes-portable.git"
    fi
fi

echo "=== Export done ==="
