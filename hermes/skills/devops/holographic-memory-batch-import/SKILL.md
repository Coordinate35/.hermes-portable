---
name: holographic-memory-batch-import
description: 将大量文本/文档批量导入 Hermes Holographic Memory (fact_store)，包括 PDF 转文本、智能分块、批量导入、HRR 向量维度兼容、分批 bundle 策略等关键坑的处理
version: 1.0
category: devops
---

# Holographic Memory 批量文本导入指南

## 适用场景

- 将成百上千个 PDF/TXT 文档的原文导入 holographic memory
- 需要快速导入大量中文文本并保持可搜索
- 遭遇 HRR 向量计算失败、维度不一致、bundle 报错等问题

## 完整流程

### 1. 环境检查

```bash
which pdftotext || sudo apt-get install -y poppler-utils
cd /home/coordinate35/hermes_data && mkdir -p pdf_extracts
```

### 2. PDF 批量转文本

```python
import subprocess, os, glob

DOCS_DIR = "/home/coordinate35/virtualbox_share/luqiyuan/docs"
OUT_DIR = "/home/coordinate35/hermes_data/pdf_extracts"

for pdf in glob.glob(os.path.join(DOCS_DIR, "*.pdf")):
    name = os.path.basename(pdf).replace(".pdf", ".txt")
    txt_path = os.path.join(OUT_DIR, name)
    subprocess.run(["pdftotext", "-layout", pdf, txt_path], check=True)
```

### 3. 修复中文生成的无意义行分符

pdftotext 对中文 PDF 会在字间插入换行。使用 Python 修复：

```python
import os

def fix_chinese_linebreaks(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    result = []
    buf = ""
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            if buf:
                result.append(buf)
                buf = ""
            result.append("")
            continue
        # 中文内容：去掉換行空白，持续累加
        if any('\u4e00' <= c <= '\u9fff' for c in line):
            buf += line
        else:
            if buf:
                result.append(buf)
                buf = ""
            result.append(line)
    if buf:
        result.append(buf)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
```

### 4. 智能分块策略

按换页符 `\f` 分割，合并小段落使每块 2500-5000 字符：

```python
def smart_chunk_file(filepath, min_chunk=2500, max_chunk=5000):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    parts = content.split('\f')

    chunks = []
    current_chunk = []
    current_len = 0

    for part in parts:
        part = part.strip()
        if len(part) < 100:   # 忽略太短的片段
            continue
        if current_len + len(part) > max_chunk and current_len >= min_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [part]
            current_len = len(part)
        else:
            current_chunk.append(part)
            current_len += len(part)
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks
```

### 5. 批量导入 holographic memory

#### 5.1 关键配置：确定 HRR 维度

数据库中可能已存在不同维度的向量，必须检查并使用相同维度：

```python
import sys, os, sqlite3
sys.path.insert(0, '/home/coordinate35/.hermes/hermes-agent')
sys.path.insert(0, '/home/coordinate35/.hermes/hermes-agent/plugins/memory/holographic')
os.environ['HERMES_HOME'] = '/home/coordinate35/.hermes'

import holographic as hrr
from store import MemoryStore

DB_PATH = '/home/coordinate35/.hermes/memory_store.db'

# 检测现有向量维度
conn = sqlite3.connect(DB_PATH)
row = conn.execute("SELECT hrr_vector FROM facts WHERE hrr_vector IS NOT NULL LIMIT 1").fetchone()
conn.close()

if row:
    vec = hrr.bytes_to_phases(row[0])
    existing_dim = vec.shape[0]    # 通常是 4096 或 1024
    print(f"Existing facts use hrr_dim={existing_dim}")
else:
    existing_dim = 4096

store = MemoryStore(db_path=DB_PATH, default_trust=0.6, hrr_dim=existing_dim)
```

#### 5.2 关键坑：隔离环境中 HRR 计算失败

`store._compute_hrr_vector()` 内部使用 `nltk.pos_tag()`，在隔离的 `execute_code` 环境中会因 nltk 资源下载失败而抛出 `LookupError`。

**解决方案：Monkey-patch 暂时禁用 HRR 计算，先快速插入所有 facts，再批量补算 HRR 向量。**

```python
# 保存原方法
orig_compute = store._compute_hrr_vector
orig_rebuild = store._rebuild_bank

# 替换为 no-op
store._compute_hrr_vector = lambda fid, content: None
store._rebuild_bank = lambda cat: None

# 快速插入所有 chunks
new_fact_ids = []
for chunk in chunks:
    content = f"[来源:{filename} 第{i+1}/{len(chunks)}段]\n\n{chunk}"
    fid = store.add_fact(content=content, category='general', tags='some,tags')
    new_fact_ids.append(fid)

# 恢复原方法
store._compute_hrr_vector = orig_compute
store._rebuild_bank = orig_rebuild
```

#### 5.3 补算 HRR 向量

```python
for i, fid in enumerate(new_fact_ids):
    row = store._conn.execute("SELECT content FROM facts WHERE fact_id = ?", (fid,)).fetchone()
    if row:
        store._compute_hrr_vector(fid, row["content"])
    if (i + 1) % 100 == 0:
        print(f"... {i+1}/{len(new_fact_ids)} vectors computed")
```

#### 5.4 关键坑：不同维度向量混合导致 bundle 失败

数据库中可能同时存在 dim=1024 和 dim=4096 的向量。
`numpy.array([...])` 打包时会报错：`inhomogeneous shape`。

**解决方案：按维度分离，分开重建 Memory Bank。**

```python
def custom_rebuild(category: str, target_dim: int) -> None:
    with store._lock:
        expected_bytes = target_dim * 8
        bank_name = f"cat:{category}"
        rows = store._conn.execute(
            """SELECT hrr_vector FROM facts
               WHERE category = ? AND hrr_vector IS NOT NULL
               AND length(hrr_vector) = ?""",
            (category, expected_bytes),
        ).fetchall()

        vectors = [hrr.bytes_to_phases(row["hrr_vector"]) for row in rows]

        # 关键坑：numpy bundle 大列表报错
        # 解决：分批 bundle，每批 500 个
        batch_size = 500
        if len(vectors) <= batch_size:
            bank_vector = hrr.bundle(*vectors)
        else:
            batch_results = []
            for i in range(0, len(vectors), batch_size):
                batch_results.append(hrr.bundle(*vectors[i:i+batch_size]))
            bank_vector = hrr.bundle(*batch_results)

        store._conn.execute(
            """INSERT OR REPLACE INTO memory_banks
               (bank_name, vector, dim, fact_count, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (bank_name, hrr.phases_to_bytes(bank_vector), target_dim, len(vectors))
        )
        store._conn.commit()

# 对每个维度分别重建
custom_rebuild('general', 4096)
custom_rebuild('general', 1024)
```

### 6. 验证

```python
conn = sqlite3.connect(DB_PATH)
total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
with_hrr = conn.execute("SELECT COUNT(*) FROM facts WHERE hrr_vector IS NOT NULL").fetchone()[0]
banks = conn.execute("SELECT bank_name, dim, fact_count FROM memory_banks").fetchall()
conn.close()
print(f"Total facts: {total}, With HRR: {with_hrr}")
for b in banks:
    print(f"  {b[0]}: dim={b[1]}, facts={b[2]}")
```

## 关键技巧

| 问题 | 原因 | 解决 |
|---|---|---|
| `_compute_hrr_vector` 报键盘中断/`LookupError` | nltk 在隔离环境中无法下载资源 | Monkey-patch 禁用，批量插入后再补算 |
| bundle 报 `inhomogeneous shape` | 数据库中混合了 1024/4096 维度向量 | 按维度过滤后分离重建 Bank |
| bundle 报 `too many positional args` | 一次传入 >~1500 个向量 | 分批 bundle，每批 500 |
| 导入超时 | 每个 chunk 都计算 HRR 很慢 | 先插入后补算，速度提升 10-50 倍 |
| `fact_store` add 报 `inhomogeneous shape` | `fact_store` 工具接口有 bug，中文/长文本触发 | 改用 Python 直接调用 `MemoryStore.add_fact()` |

### 特别重要：`fact_store` 工具 `add` 操作在中文内容下的 bug

**现象**：调用 `fact_store(action="add", content="...")` 时，即使 `content` 是合法字符串，也会报错：
```
setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions.
```

**根因**：`fact_store` 工具接口层在处理中文内容（或较长内容）时，向 HRR 计算层传递的参数格式有问题，导致 numpy 数组构造失败。这是工具层的 bug，不是 holographic memory 插件本身的问题。

**验证**：直接通过 Python 调用 `MemoryStore.add_fact()` 完全正常，同一条中文内容可以成功写入。

**解决**：批量导入时，不要走 `fact_store` 工具，而是直接在 `execute_code` 中：

```python
import sys
sys.path.insert(0, '/home/coordinate35/.hermes/hermes-agent')
from plugins.memory.holographic.store import MemoryStore

store = MemoryStore(
    db_path='/home/coordinate35/.hermes/memory_store.db',
    default_trust=0.7,
    hrr_dim=4096
)

for chunk in chunks:
    fid = store.add_fact(content=chunk, category='general', tags='tag1,tag2')
    print(f"Inserted fact_id={fid}")
```

**注意**：如果同时遇到 nltk 资源问题，可以结合上面的 Monkey-patch 策略，先禁用 `_compute_hrr_vector`，批量插入后再补算。

## 典型用法

```python
FILES_META = {
    '文档名.txt': {'tags': '标签1,标签2', 'category': 'general'},
}

for fname, meta in FILES_META.items():
    filepath = os.path.join(BASE_DIR, fname)
    chunks = smart_chunk_file(filepath)
    for i, chunk in enumerate(chunks):
        content = f"[来源:{fname} 第{i+1}/{len(chunks)}段]\n\n{chunk}"
        store.add_fact(content=content, category=meta['category'], tags=meta['tags'])
```