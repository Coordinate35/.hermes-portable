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
        f.write('INSERT INTO entities VALUES(' + ','.join(vals) + ');\\n')  # avoid nested same-quote f-string (Py<3.12)
    
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

SRC_HERMES="$HOME/.hermes"
SRC_DATA="$HOME/hermes_data"
DST="$HOME/.hermes-portable"

echo "=== Hermes Portable Export ==="

# 1. 复制文本配置
cp "$SRC_HERMES/SOUL.md" "$DST/hermes/"
rsync -a --delete "$SRC_HERMES/memories/" "$DST/hermes/memories/"
rsync -a --delete --exclude='__pycache__' "$SRC_HERMES/skills/" "$DST/hermes/skills/"
mkdir -p "$DST/hermes/cron"
cp "$SRC_HERMES/cron/jobs.json" "$DST/hermes/cron/"
rsync -a --delete --exclude='__pycache__' "$SRC_HERMES/scripts/" "$DST/hermes/scripts/"

# 2. 脱敏 config.yaml
python3 -c "
import re
with open('$SRC_HERMES/config.yaml') as f: raw = f.read()
redacted = re.sub(r'^(\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', raw, flags=re.MULTILINE)
redacted = re.sub(r'^(-\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', redacted, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*api_secret:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_SECRET__', redacted, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*token:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_TOKEN__', redacted, flags=re.MULTILINE)
with open('$DST/hermes/config.yaml', 'w') as f:
    f.write('# WARNING: Secrets redacted. Fill placeholders before use.\n')
    f.write(redacted)
"

# 3. 导出全息记忆（使用 Python sqlite3，不依赖 sqlite3 CLI）
echo "[*] Exporting memory store (text-only)..."
python3 -c "
import sqlite3, os, sys, datetime

db = os.path.expanduser('$SRC_HERMES/memory_store.db')
dst = os.path.expanduser('$DST/hermes/memory_store_core.sql')
if not os.path.exists(db):
    print('[!] memory_store.db not found'); sys.exit(0)

conn = sqlite3.connect(db)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM facts')
fact_count = cursor.fetchone()[0]

skip_tables = {'facts_fts', 'facts_fts_config', 'facts_fts_data',
               'facts_fts_docsize', 'facts_fts_idx', 'sqlite_sequence'}

with open(dst, 'w') as f:
    f.write('-- Hermes Holographic Memory Export (text-only)\n')
    f.write(f'-- Facts count: {fact_count}\n')
    f.write(f'-- Exported: {datetime.datetime.now().isoformat()}\n')
    f.write('BEGIN TRANSACTION;\n\n')

    for name, sql in cursor.execute(\"SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name\"):
        if name in skip_tables or not sql: continue
        f.write(f'{sql};\n')

    cursor.execute('''SELECT fact_id, content, category, tags, trust_score,
               retrieval_count, helpful_count, created_at, updated_at
        FROM facts ORDER BY fact_id''')
    for row in cursor.fetchall():
        vals = ['NULL' if v is None else repr(v) if isinstance(v, str) else str(v) for v in row]
        f.write('INSERT INTO facts(fact_id, content, category, tags, trust_score, '
                'retrieval_count, helpful_count, created_at, updated_at) '
                'VALUES(' + ','.join(vals) + ');\n')

    for row in cursor.execute('SELECT * FROM entities ORDER BY entity_id'):
        vals = ['NULL' if v is None else repr(v) if isinstance(v, str) else str(v) for v in row]
        f.write('INSERT INTO entities VALUES(' + ','.join(vals) + ');\n')

    for row in cursor.execute('SELECT * FROM fact_entities ORDER BY rowid'):
        vals = ['NULL' if v is None else repr(v) if isinstance(v, str) else str(v) for v in row]
        f.write('INSERT INTO fact_entities VALUES(' + ','.join(vals) + ');\n')

    for row in cursor.execute(
        'SELECT bank_id, bank_name, dim, fact_count, updated_at FROM memory_banks ORDER BY bank_id'):
        vals = ['NULL' if v is None else repr(v) if isinstance(v, str) else str(v) for v in row]
        f.write('INSERT INTO memory_banks(bank_id, bank_name, dim, fact_count, updated_at) '
                'VALUES(' + ','.join(vals) + ');\n')

    for (sql,) in cursor.execute(\"SELECT sql FROM sqlite_master WHERE type='index' ORDER BY name\"):
        if sql and not any(s in sql for s in skip_tables):
            f.write(f'{sql};\n')
    f.write('\nCOMMIT;\n')
conn.close()
print(f'[+] memory_store_core.sql ({fact_count} facts)')
"

# 4. 备份 hermes_data（用户工作目录）
if [[ -d "$SRC_DATA" ]]; then
    mkdir -p "$DST/hermes_data"
    rsync -a --delete \
        --exclude='venv' --exclude='.venv' --exclude='env' \
        --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' \
        --exclude='logs' --exclude='*.log' \
        --exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' \
        --exclude='.DS_Store' --exclude='*.tmp' --exclude='*.temp' \
        --exclude='*.bak' --exclude='*.backup' \
        --exclude='cache' --exclude='node_modules' \
        --exclude='*.onnx' --exclude='*.bin' \
        --exclude='*.pt' --exclude='*.pth' --exclude='*.safetensors' \
        "$SRC_DATA/" "$DST/hermes_data/"
    echo "[+] hermes_data/ backed up"
fi

# 5. Git 提交
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
DST_HERMES="${1:-$HOME/.hermes}"
DST_DATA="${2:-$HOME/hermes_data}"

echo "=== Hermes Portable Import ==="

# 1. 恢复 ~/.hermes 配置
mkdir -p "$DST_HERMES"
cp "$SCRIPT_DIR/hermes/SOUL.md" "$DST_HERMES/"
rsync -a --delete "$SCRIPT_DIR/hermes/memories/" "$DST_HERMES/memories/"
rsync -a --delete "$SCRIPT_DIR/hermes/skills/" "$DST_HERMES/skills/"
mkdir -p "$DST_HERMES/cron"
cp "$SCRIPT_DIR/hermes/cron/jobs.json" "$DST_HERMES/cron/"
rsync -a --delete --exclude='__pycache__' "$SCRIPT_DIR/hermes/scripts/" "$DST_HERMES/scripts/"
cp "$SCRIPT_DIR/hermes/config.yaml" "$DST_HERMES/config.yaml"
echo "[!] 请编辑 $DST_HERMES/config.yaml 填入你的 API Key"

# 2. 恢复全息记忆（使用 Python，不依赖 sqlite3 CLI）
SQL_FILE="$SCRIPT_DIR/hermes/memory_store_core.sql"
if [[ -f "$SQL_FILE" ]]; then
    rm -f "$DST_HERMES/memory_store.db"
    python3 -c "
import sqlite3
with open('$SQL_FILE', 'r') as f: sql = f.read()
conn = sqlite3.connect('$DST_HERMES/memory_store.db')
conn.executescript(sql)
conn.commit(); conn.close()
"
    echo "[+] 全息记忆文本数据导入完成"

    # 3. 重建 HRR 向量（优先使用 Hermes venv 的 Python）
    echo "[*] 正在重建 HRR 向量..."
    if [[ -f "$SCRIPT_DIR/scripts/rebuild_vectors.py" ]]; then
        HERMES_PYTHON="$DST_HERMES/hermes-agent/venv/bin/python"
        if [[ -f "$HERMES_PYTHON" ]]; then
            "$HERMES_PYTHON" "$SCRIPT_DIR/scripts/rebuild_vectors.py"
        else
            python3 "$SCRIPT_DIR/scripts/rebuild_vectors.py"
        fi
    else
        echo "[!] 未找到 rebuild_vectors.py，跳过向量重建"
    fi
fi

# 4. 恢复 ~/hermes_data
if [[ -d "$SCRIPT_DIR/hermes_data" ]]; then
    mkdir -p "$DST_DATA"
    rsync -a --delete "$SCRIPT_DIR/hermes_data/" "$DST_DATA/"
    echo "[+] hermes_data/ 恢复完成"
fi

# 5. state.db 不复原

echo "[i] state.db 不复原（会话历史从头开始）"
echo "=== 导入完成 ==="
```

### `~/.hermes-portable/scripts/rebuild_vectors.py`

单独维护的重建脚本，绕开 Python 包名限制，自动检测 Hermes venv：

```python
#!/usr/bin/env python3
import os, sys, shutil, tempfile, importlib.util, subprocess

HERMES_HOME = os.path.expanduser("~/.hermes")
DB_PATH = os.path.join(HERMES_HOME, "memory_store.db")
SRC_DIR = os.path.join(HERMES_HOME, "hermes-agent", "plugins", "memory", "holographic")
HERMES_VENV_PYTHON = os.path.join(HERMES_HOME, "hermes-agent", "venv", "bin", "python")

def _ensure_numpy() -> bool:
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        pass
    if os.path.exists(HERMES_VENV_PYTHON):
        result = subprocess.run(
            [HERMES_VENV_PYTHON, "-c", "import numpy; print('ok')"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "ok" in result.stdout:
            os.execv(HERMES_VENV_PYTHON, [HERMES_VENV_PYTHON] + sys.argv)
    # 尝试安装 numpy 作为最后手段
    for pip_cmd in [f"{sys.executable} -m pip", "pip3", "pip"]:
        if os.system(f"{pip_cmd} install numpy -q 2>/dev/null") == 0:
            import importlib; importlib.invalidate_caches()
            try: import numpy; return True  # noqa: F401
            except ImportError: continue
    return False

def load_module_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod

def main() -> int:
    if not _ensure_numpy(): return 1
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_dir = os.path.join(tmpdir, "holo_rebuild")
        os.makedirs(pkg_dir, exist_ok=True)
        for fname in ["store.py", "holographic.py"]:
            shutil.copy2(os.path.join(SRC_DIR, fname), pkg_dir)
        hrr_mod = load_module_from_path("holo_hrr", os.path.join(pkg_dir, "holographic.py"))
        sys.modules["holographic"] = hrr_mod
        store_mod = load_module_from_path("holo_store", os.path.join(pkg_dir, "store.py"))
        store = store_mod.MemoryStore(db_path=DB_PATH)
        count = store.rebuild_all_vectors()
        store.close()
        print(f"[+] Rebuilt {count} HRR vectors")
    return 0

if __name__ == "__main__": sys.exit(main())
```

## .gitignore 模板

```gitignore
# Secrets
.env
*.key
*.pem
.env.real

# OS / Editor
.DS_Store
*.swp
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo

# SQLite binaries（使用 SQL dump 代替）
*.db
*.db-wal
*.db-shm
*.db-journal

# 旧版 V1 二进制备份
*.db.gz
*.db.gz.part-*

# 虚拟环境（可重建）
venv/
.venv/
env/

# 日志与缓存
logs/
*.log
cache/
image_cache/
audio_cache/
*.cache
node_modules/

# 会话状态（不移植）
state.db*
sessions/
checkpoints/

# 临时文件
*.tmp
*.temp
*.bak
*.backup

# ML 模型权重（可重新下载，常超 100MB GitHub 限制）
*.onnx
*.bin
*.pt
*.pth
*.safetensors
```

## 实际部署参考

具体环境可能遇到的问题（sqlite3 CLI 缺失、numpy 仅在 venv 中等）及解决方案，见 `references/environment-adaptations.md`。

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
10. **环境适配** — 不同系统可能存在 `sqlite3` CLI 缺失、`numpy` 仅装在 Hermes venv 中等差异，详见 `references/environment-adaptations.md`
11. **ML 模型文件勿入库** — `.onnx` / `.bin` / `.pt` / `.pth` / `.safetensors` 等机器学习模型权重常超过 GitHub 100MB 单文件限制，会导致 `pre-receive hook declined` 推送失败。export.sh 已默认排除这些格式，模型需在新机器上重新下载。若历史中已污染大文件，用 `git filter-branch --index-filter 'git rm --cached --ignore-unmatch <path>' --prune-empty -- --all` 清理后再推送。

```bash
# 删除 V1 旧版二进制分卷备份（已废弃，新版使用文本 SQL）
rm -f ~/.hermes-portable/memory_store.db.gz.part-*
rm -f ~/.hermes-portable/memory_store.db.gz
```
