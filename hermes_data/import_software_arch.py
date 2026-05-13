#!/usr/bin/env python3
"""
将 /home/coordinate35/virtualbox_share/software_arch/ 中的 .rst 文档
导入到 Hermes holographic memory 数据库中。

复用自 import_daodejing.py，仅修改源目录和类别。
"""

import os
import sys
import glob
import re
import sqlite3

# ---------------------------------------------------------------------------
# 1. 加载 MemoryStore
# ---------------------------------------------------------------------------
PLUGIN_DIR = os.path.expanduser("~/.hermes/hermes-agent/plugins/memory/holographic")
sys.path.insert(0, PLUGIN_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location("store", os.path.join(PLUGIN_DIR, "store.py"))
store_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store_mod)

DB_PATH = os.path.expanduser("~/.hermes/memory_store.db")
SOURCE_DIR = "/home/coordinate35/virtualbox_share/software_arch/"
CATEGORY = "software_arch"

# ---------------------------------------------------------------------------
# 2. 工具函数
# ---------------------------------------------------------------------------

def clean_rst(text: str) -> str:
    """移除 RST 标记，保留可读内容。"""
    lines = text.splitlines()
    cleaned = []
    skip_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".. figure::"):
            skip_block = True
            continue
        if stripped.startswith(".. include::"):
            continue
        if stripped.startswith(":Authors:") or stripped.startswith(":Version:"):
            continue
        if stripped.startswith(".. [") and "]" in stripped:
            cleaned.append(line)
            continue
        if stripped.startswith(".. ") and not stripped.startswith(".. ["):
            continue
        if re.match(r"^[\*\=\-\~\^\"\']+$", stripped):
            continue
        if skip_block:
            if stripped == "" or not line.startswith("        "):
                skip_block = False
            else:
                continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def split_into_chunks(text: str, max_len: int = 1500, overlap: int = 100) -> list:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(p) > max_len:
            sentences = re.split(r"(?<=[。．.!?])　*", p)
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if len(current) + len(s) + 1 <= max_len:
                    current = (current + "\n" + s).strip() if current else s
                else:
                    if current:
                        chunks.append(current)
                    current = s
        else:
            if len(current) + len(p) + 2 <= max_len:
                current = (current + "\n\n" + p).strip() if current else p
            else:
                if current:
                    chunks.append(current)
                current = p
    if current:
        chunks.append(current)
    return chunks


def extract_title(text: str, filename: str) -> str:
    m = re.search(r"^\d+\.\s*(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    base = os.path.splitext(os.path.basename(filename))[0]
    return base


# ---------------------------------------------------------------------------
# 3. 主导入逻辑
# ---------------------------------------------------------------------------

def main():
    store = store_mod.MemoryStore(
        db_path=DB_PATH,
        default_trust=0.7,
        hrr_dim=4096
    )

    pattern = os.path.join(SOURCE_DIR, "**", "*.rst")
    files = sorted(glob.glob(pattern, recursive=True))

    print(f"Found {len(files)} .rst files in {SOURCE_DIR}")

    total_facts = 0
    skipped = 0
    errors = 0

    for fpath in files:
        rel = os.path.relpath(fpath, SOURCE_DIR)
        if rel.startswith("_static"):
            continue

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            print(f"  [SKIP] Cannot read {rel}: {e}")
            skipped += 1
            continue

        cleaned = clean_rst(raw)
        if not cleaned:
            print(f"  [SKIP] Empty after cleaning: {rel}")
            skipped += 1
            continue

        title = extract_title(raw, rel)
        tags = f"software_arch,{title.replace(' ', '_').replace('、', '')}"
        tags = tags[:200]

        chunks = split_into_chunks(cleaned, max_len=1500)
        print(f"  {rel}: {len(chunks)} chunk(s), title='{title}'")

        for idx, chunk in enumerate(chunks):
            if len(chunks) > 1:
                content = f"[来源: {rel} - {title} 第{idx+1}/{len(chunks)}块]\n\n{chunk}"
            else:
                content = f"[来源: {rel} - {title}]\n\n{chunk}"

            try:
                fid = store.add_fact(content, category=CATEGORY, tags=tags)
                total_facts += 1
            except Exception as e:
                print(f"    [ERROR] add_fact failed for chunk {idx+1} of {rel}: {e}")
                errors += 1

    print("\n" + "=" * 50)
    print(f"导入完成: 共 {total_facts} 条 facts 导入成功")
    print(f"跳过: {skipped} 个文件")
    print(f"失败: {errors} 个 chunks")

    # 验证总数
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM facts WHERE category='{CATEGORY}';")
    count = cur.fetchone()[0]
    conn.close()
    print(f"数据库中 category='{CATEGORY}' 的 facts 总数: {count}")

    # 修复 HRR 向量
    print("\n正在重建所有 HRR 向量...")
    processed = store.rebuild_all_vectors()
    print(f"已处理 {processed} 条 facts 的 HRR 向量")

    store.close()


if __name__ == "__main__":
    main()
