---
name: hermes-agent-github-backup
description: |
  将 Hermes Agent 的完整配置（含全息记忆数据库）备份到 GitHub，
  实现跨机器同步恢复。包含自动脱敏、hrr_vector 显式重建方案。
version: 2.0
author: Hermes Agent
metadata:
  hermes:
    tags: [hermes, backup, sync, github, sqlite, holographic-memory]
    related_skills: [github-repo-management, github-auth]
---

# Hermes Agent GitHub 备份与跨机器同步（V2）

将 Hermes Agent 的完整配置、人格、记忆、技能和全息记忆数据库备份到 GitHub 私有仓库，以便在任何电脑上快速恢复。

## 核心设计决策（经过实验验证）

### 为什么不用 .db.gz 二进制？

把 `memory_store.db` gzip 压缩后放进 Git，**任何微小的改动都会导致整个 .gz 文件完全不同**。Git 对二进制无法做 delta，每天备份会让仓库按 ~240MB/天的速度膨胀，一年 ~87GB。

### 为什么不用 `sqlite3 .dump` 全量导出？

全量 SQL dump（含 `hrr_vector` 列）约 **488MB**。因为 `hrr_vector` 是二进制向量（每条事实 ~8KB BLOB），在 dump 中变成十六进制字符串后膨胀，占 dump 体积的 **97%**。这 7857 段伪随机十六进制字符串让 Git delta 完全失效，每天增量 ~275MB。

### 正确方案：排除 hrr_vector 的全量 SQL dump

`hrr_vector` 是从 `content` 派生的**可重算数据**。排除它之后，全量 dump 仅 **~17MB**，其中真正的文本内容 ~7MB。Git delta 对这个规模的文本非常高效：

| 指标 | 含 hrr_vector | **不含 hrr_vector** |
|:---|:---:|:---:|
| 工作区文件 | 488MB | **~17MB** |
| Git 初始 pack | 276MB | **~6MB** |
| 每天 10 条增量 | ~275MB | **~50KB** |
| 30 天后 gc --aggressive | 262MB | **~7MB** |
| 一年总量 | 100GB | **~20MB** |

恢复时导入 SQL，**显式调用 `rebuild_all_vectors()` 重建** `hrr_vector`。

## 解决方案

在 `~/.hermes-portable/` 创建一个专用的 Git 仓库，包含以下内容：

| 内容 | 备份方式 |
|------|---------|
| `SOUL.md` | 完整复制 |
| `memories/` | 完整复制 |
| `skills/` | 完整复制 |
| `cron/jobs.json` | 完整复制 |
| `scripts/` | 完整复制 |
| `config.yaml` | 完整复制，自动脱敏 API Key |
| `memory_store_core.sql` | **全量 SQL dump，排除 BLOB 列** |
| `state.db` | ❌ **不备份**（会话历史，新机器从头开始） |

排除：`.env`、缓存目录、Python 缓存、大型日志、所有 `.db` 文件、FTS 虚拟表

## 安全脱敏规则

运行 `export.sh` 时自动执行：
```python
import re

# 替换 config.yaml 中所有 api_key 字段
redacted = re.sub(r'^(\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', raw, flags=re.MULTILINE)
redacted = re.sub(r'^(-\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', redacted, flags=re.MULTILINE)
```

`.env` 文件仅导出键名模板，值替换为占位符。

## 全息记忆数据库备份（关键优化）

### 为什么不能直接压缩 .db？

`.db` 是 SQLite 二进制文件，gzip 压缩后放进 Git——**任何一字节改动都会让整个 .gz 流重新生成**。Git 对二进制没有 delta 能力，每天备份 = 每天存一份完整的 ~240MB。

### 为什么不能直接 `sqlite3 .dump`？

全量 dump 含 `hrr_vector`时，这个二进制向量会变成十六进制字符串。导致 dump 达 488MB，其中 97% 是"伪随机十六进制"，Git delta 完全失效。

### 正确方法：排除派生 BLOB 的全量 dump

排除 `hrr_vector` 列和 FTS 虚拟表后，全量 dump 仅 **~17MB**，每天增量 **~50KB**，无需 Git LFS。

**注意：** `hrr_vector` 不会自动重建。恢复后必须显式调用 `MemoryStore.rebuild_all_vectors()` 重新计算。

### 导出脚本中数据库处理

```bash
# 不要这样做（二进制 .gz，Git delta 失效）
# gzip -6 -c ~/.hermes/memory_store.db > memory_store.db.gz

# 这样做（排除 BLOB 列的全量 SQL dump，~17MB，Git delta 极效）
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('~/.hermes/memory_store.db'))

# 手动导出：schema 保留（含 hrr_vector BLOB 列），但 INSERT 跳过该列
skip_tables = {'facts_fts', 'facts_fts_config', 'facts_fts_data', 
               'facts_fts_docsize', 'facts_fts_idx', 'sqlite_sequence'}

with open(os.path.expanduser('~/.hermes-portable/memory_store_core.sql'), 'w') as f:
    cursor = conn.cursor()
    
    # 1. Schema（保留完整表结构，包括 hrr_vector BLOB 列）
    for name, sql in cursor.execute(
        \"SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name\"
    ):
        if name in skip_tables:
            continue
        if sql:
            f.write(f'{sql};\\n')
    
    # 2. facts — 只插入文本列（跳过 hrr_vector BLOB）
    cursor.execute('''
        SELECT fact_id, content, category, tags, trust_score,
               retrieval_count, helpful_count, created_at, updated_at
        FROM facts ORDER BY fact_id
    ''')
    for row in cursor.fetchall():
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write(f'INSERT INTO facts(fact_id, content, category, tags, trust_score, retrieval_count, helpful_count, created_at, updated_at) VALUES({','.join(vals)});\\n')
    
    # 3. entities
    for row in cursor.execute('SELECT * FROM entities ORDER BY entity_id'):
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write(f'INSERT INTO entities VALUES({','.join(vals)});\\n')
    
    # 4. fact_entities
    for row in cursor.execute('SELECT * FROM fact_entities ORDER BY rowid'):
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write(f'INSERT INTO fact_entities VALUES({','.join(vals)});\\n')
    
    # 5. memory_banks — 只插入文本列（跳过 vector BLOB）
    cursor.execute('SELECT bank_id, bank_name, dim, fact_count, updated_at FROM memory_banks ORDER BY bank_id')
    for row in cursor.fetchall():
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write(f'INSERT INTO memory_banks(bank_id, bank_name, dim, fact_count, updated_at) VALUES({','.join(vals)});\\n')
    
    # 6. Indexes
    for (sql,) in cursor.execute(\"SELECT sql FROM sqlite_master WHERE type='index' ORDER BY name\"):
        if sql and not any(s in sql for s in skip_tables):
            f.write(f'{sql};\\n')
    
    f.write('COMMIT;\\n')

conn.close()
"
```

## 完整脚本模板

### `~/.hermes-portable/export.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SRC="$HOME/.hermes"
DST="$HOME/.hermes-portable"

echo "=== Hermes Portable Export ==="

# 1. 复制文本配置
cp "$SRC/SOUL.md" "$DST/"
rsync -a --delete "$SRC/memories/" "$DST/memories/"
rsync -a --delete "$SRC/skills/" "$DST/skills/"
mkdir -p "$DST/cron"
cp "$SRC/cron/jobs.json" "$DST/cron/"
rsync -a --delete --exclude='__pycache__' "$SRC/scripts/" "$DST/scripts/"

# 2. 脱敏 config.yaml
python3 -c "
import re
with open('$SRC/config.yaml') as f: raw = f.read()
redacted = re.sub(r'^(\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', raw, flags=re.MULTILINE)
redacted = re.sub(r'^(-\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', redacted, flags=re.MULTILINE)
with open('$DST/config.yaml', 'w') as f:
    f.write('# WARNING: Secrets redacted. Fill placeholders before use.\n')
    f.write(redacted)
"

# 3. 导出全息记忆（排除 hrr_vector / memory_banks.vector BLOB 列）
echo "[*] Exporting memory store (text-only, ~17MB)..."
python3 -c "
import sqlite3, os

db = os.path.expanduser('$SRC/memory_store.db')
conn = sqlite3.connect(db)
cursor = conn.cursor()

skip_tables = {'facts_fts', 'facts_fts_config', 'facts_fts_data',
               'facts_fts_docsize', 'facts_fts_idx', 'sqlite_sequence'}

with open(os.path.expanduser('$DST/memory_store_core.sql'), 'w') as f:
    # Schema
    for name, sql in cursor.execute(\"SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name\"):
        if name in skip_tables:
            continue
        if sql:
            f.write(f'{sql};\n')
    
    # facts (no hrr_vector)
    cursor.execute('''
        SELECT fact_id, content, category, tags, trust_score,
               retrieval_count, helpful_count, created_at, updated_at
        FROM facts ORDER BY fact_id
    ''')
    for row in cursor.fetchall():
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write('INSERT INTO facts(fact_id, content, category, tags, trust_score, ' +
                'retrieval_count, helpful_count, created_at, updated_at) ' +
                'VALUES(' + ','.join(vals) + ');\n')
    
    # entities
    for row in cursor.execute('SELECT * FROM entities ORDER BY entity_id'):
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write('INSERT INTO entities VALUES(' + ','.join(vals) + ');\n')
    
    # fact_entities
    for row in cursor.execute('SELECT * FROM fact_entities ORDER BY rowid'):
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write('INSERT INTO fact_entities VALUES(' + ','.join(vals) + ');\n')
    
    # memory_banks (no vector BLOB)
    for row in cursor.execute(
        'SELECT bank_id, bank_name, dim, fact_count, updated_at FROM memory_banks ORDER BY bank_id'
    ):
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, str): vals.append(repr(v))
            else: vals.append(str(v))
        f.write('INSERT INTO memory_banks(bank_id, bank_name, dim, fact_count, updated_at) ' +
                'VALUES(' + ','.join(vals) + ');\n')
    
    # indexes
    for (sql,) in cursor.execute(\"SELECT sql FROM sqlite_master WHERE type='index' ORDER BY name\"):
        if sql and not any(s in sql for s in skip_tables):
            f.write(f'{sql};\n')
    
    f.write('\nCOMMIT;\n')

conn.close()
"

# 4. Git 提交
cd "$DST"
git add -A
git commit -m "sync: $(date +%Y-%m-%d-%H:%M)" || true
git push origin main || true

echo "=== Export done ==="
```

### `~/.hermes-portable/import.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="${1:-$HOME/.hermes}"

echo "=== Hermes Portable Import ==="

mkdir -p "$DST"

# 1. 恢复文本配置
cp "$SCRIPT_DIR/SOUL.md" "$DST/"
rsync -a --delete "$SCRIPT_DIR/memories/" "$DST/memories/"
rsync -a --delete "$SCRIPT_DIR/skills/" "$DST/skills/"
mkdir -p "$DST/cron"
cp "$SCRIPT_DIR/cron/jobs.json" "$DST/cron/"
rsync -a --delete --exclude='__pycache__' "$SCRIPT_DIR/scripts/" "$DST/scripts/"

# 2. 恢复配置（需要手动填入 API Key）
cp "$SCRIPT_DIR/config.yaml" "$DST/config.yaml"
echo "[!] 请编辑 $DST/config.yaml 填入你的 API Key"

# 3. 恢复全息记忆
if [[ -f "$SCRIPT_DIR/memory_store_core.sql" ]]; then
    rm -f "$DST/memory_store.db"
    sqlite3 "$DST/memory_store.db" < "$SCRIPT_DIR/memory_store_core.sql"
    echo "[+] 全息记忆文本数据导入完成"
    
    # 显式重建 hrr_vector 和 memory_banks.vector
    echo "[*] 正在重建 HRR 向量（约几秒到几十秒）..."
    python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/hermes-agent'))
from hermes-agent.plugins.memory.holographic.store import MemoryStore

store = MemoryStore(db_path=os.path.expanduser('$DST/memory_store.db'))
count = store.rebuild_all_vectors()
print(f'[+] Rebuilt HRR vectors for {count} facts')
store.close()
"
    echo "[+] HRR 向量重建完成"
fi

# 4. state.db 不复原——会话历史从头开始
echo "[i] state.db 不复原（会话历史从头开始）"

echo "=== 导入完成 ==="
echo "请安装 Hermes Agent 本体，填入 API Key 后启动。"
```

## .gitignore 模板

```gitignore
# Secrets
.env
*.key
*.pem

# OS / Editor
.DS_Store
*.swp
.vscode/
.idea/

# Python
__pycache__/
*.pyc

# 所有 SQLite 二进制文件（不应直接入库）
*.db
*.db-wal
*.db-shm

# 旧版 V1 残留：二进制 gzip 分卷（不再使用，Git delta 失效）
*.db.gz
*.db.gz.part-*

# state.db 不备份（会话历史，新机器重新开始）
state.db*

# 临时 SQL dump
*.sql.tmp
```

## 快速启用流程

```bash
# 第一次：初始化备份目录
mkdir -p ~/.hermes-portable/{skills,memories,cron,scripts}
cd ~/.hermes-portable && git init && git branch -m main

# 编写 export.sh / import.sh，创建 .gitignore
# 按上文的脚本模板填充后

# 执行第一次导出
chmod +x export.sh && ./export.sh

# 在 GitHub 创建私有仓库（不要勾选 README）
# 然后推送
git remote add origin https://github.com/YOUR_USER/hermes-portable.git
git branch -M main
git push -u origin main
```

## 恢复到新机器

```bash
git clone https://github.com/YOUR_USER/hermes-portable.git ~/.hermes-portable
cd ~/.hermes-portable && ./import.sh
# 按提示填入 API Key，安装 Hermes 本体后启动
```

## 注意事项

1. **必须是私有仓库** — 即使脱敏了，配置信息仍推荐保密
2. **定期同步** — 修改技能、记忆后运行 `./export.sh`
3. **不能直接存 .db.gz** — gzip 二进制在 Git 中无法 delta，每天会膨胀 ~240MB
4. **不能直接 sqlite3 dump 全量** — `hrr_vector` 占 dump 体积 97%，Git delta 失效
5. **排除 hrr_vector 的 dump 是正解** — ~17MB 文件，每天增量 ~50KB，无需 LFS
6. **state.db 不备份** — 会话历史是临时日志，新机器重新开始更干净
7. **恢复后必须显式重建 hrr_vector** — `import.sh` 中已包含 `rebuild_all_vectors()` 调用，不要跳过
8. **memory_banks.vector 也需要重建** — `rebuild_all_vectors()` 会自动处理
9. **V1 旧版残留清理** — 如果 `~/.hermes-portable/` 下有 `memory_store.db.gz.part-*` 等旧版二进制分卷文件，这是已废弃的 V1 方案残留，可安全删除以释放空间

```bash
# 删除 V1 旧版二进制分卷备份（已废弃，新版使用文本 SQL）
rm -f ~/.hermes-portable/memory_store.db.gz.part-*
rm -f ~/.hermes-portable/memory_store.db.gz
```
