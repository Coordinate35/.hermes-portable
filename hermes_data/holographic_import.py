#!/usr/bin/env python3
"""
批量导入数据到 Holographic Memory Provider

用法:
    python holographic_import.py --dir /path/to/docs       # 导入目录下所有文本文件
    python holographic_import.py --file /path/to/file.md   # 导入单个文件
    python holographic_import.py --json /path/to/data.json # 导入JSON格式事实
    python holographic_import.py --memory                  # 导入现有 MEMORY.md/USER.md
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Holographic Memory 数据库路径
DEFAULT_DB_PATH = Path.home() / ".hermes" / "memory_store.db"


def get_db_path() -> Path:
    """获取 holographic 数据库路径"""
    # 从 config.yaml 读取
    config_path = Path.home() / ".hermes" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            db_path = config.get("plugins", {}).get("hermes-memory-store", {}).get("db_path")
            if db_path:
                db_path = db_path.replace("$HERMES_HOME", str(Path.home() / ".hermes"))
                db_path = db_path.replace("${HERMES_HOME}", str(Path.home() / ".hermes"))
                return Path(db_path)
        except Exception:
            pass
    return DEFAULT_DB_PATH


def init_database(db_path: Path):
    """确保数据库表结构存在"""
    # 展开用户主目录
    db_path = Path(db_path).expanduser()
    # 确保父目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建 facts 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            tags TEXT,
            trust_score REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP
        )
    """)

    # 创建实体关联表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_entities (
            fact_id INTEGER,
            entity TEXT,
            FOREIGN KEY (fact_id) REFERENCES facts(id)
        )
    """)

    # 创建 HRR 向量表（用于语义搜索）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_vectors (
            fact_id INTEGER,
            vector BLOB,
            FOREIGN KEY (fact_id) REFERENCES facts(id)
        )
    """)

    # 创建 FTS5 全文搜索表
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
            content,
            content_rowid=id
        )
    """)

    conn.commit()
    conn.close()
    print(f"✓ 数据库初始化完成: {db_path}")


def extract_entities(text: str) -> List[str]:
    """从文本中提取实体（简单实现）"""
    # 匹配大写字母开头的单词组合（可能是专有名词）
    entities = re.findall(r'[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*', text)
    # 匹配引号内的内容
    quoted = re.findall(r'["""]([^"""]+)["""]', text)
    # 匹配特定模式
    patterns = re.findall(r'(投资|分析|框架|策略|周期|通胀|利率|GDP|CPI|M2|LPR)', text)

    all_entities = list(set(entities + quoted + patterns))
    return [e for e in all_entities if len(e) > 1][:10]  # 最多10个实体


def generate_hrr_vector(text: str, dim: int = 4096) -> bytes:
    """生成 HRR 向量（简化版，使用随机投影）"""
    import numpy as np

    # 使用文本哈希生成确定性向量
    np.random.seed(hash(text) % (2**32))
    vector = np.random.randn(dim).astype(np.float32)
    vector = vector / np.linalg.norm(vector)  # 归一化
    return vector.tobytes()


def add_fact(
    db_path: Path,
    content: str,
    category: str = "general",
    tags: str = "",
    trust_score: float = 0.5
) -> int:
    """添加单个事实到数据库"""
    db_path = Path(db_path).expanduser()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 插入事实
    cursor.execute("""
        INSERT INTO facts (content, category, tags, trust_score)
        VALUES (?, ?, ?, ?)
    """, (content, category, tags, trust_score))

    fact_id = cursor.lastrowid

    # 提取并存储实体
    entities = extract_entities(content)
    for entity in entities:
        cursor.execute(
            "INSERT INTO fact_entities (fact_id, entity) VALUES (?, ?)",
            (fact_id, entity)
        )

    # 生成并存储 HRR 向量
    try:
        vector = generate_hrr_vector(content)
        cursor.execute(
            "INSERT INTO fact_vectors (fact_id, vector) VALUES (?, ?)",
            (fact_id, vector)
        )
    except ImportError:
        pass  # numpy 未安装时跳过

    # 更新 FTS 索引
    cursor.execute(
        "INSERT INTO facts_fts (rowid, content) VALUES (?, ?)",
        (fact_id, content)
    )

    conn.commit()
    conn.close()
    return fact_id


def extract_docx_text(file_path: Path) -> str:
    """从 docx 文件中提取文本（不依赖外部库）"""
    import zipfile
    from xml.etree import ElementTree as ET

    try:
        # docx 是 zip 文件，word/document.xml 包含文本
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_content = z.read('word/document.xml')

        # 解析 XML
        tree = ET.fromstring(xml_content)
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }

        # 提取所有 <w:t> 元素的文本
        paragraphs = []
        current_para = []

        for elem in tree.iter():
            if elem.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t':
                if elem.text:
                    current_para.append(elem.text)
            elif elem.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p':
                if current_para:
                    para_text = ''.join(current_para).strip()
                    if para_text:
                        paragraphs.append(para_text)
                    current_para = []

        # 处理最后一个段落
        if current_para:
            para_text = ''.join(current_para).strip()
            if para_text:
                paragraphs.append(para_text)

        return '\n\n'.join(paragraphs)

    except zipfile.BadZipFile:
        print(f"  ✗ 不是有效的 docx 文件")
        return ""
    except KeyError:
        print(f"  ✗ docx 文件缺少 document.xml")
        return ""
    except Exception as e:
        print(f"  ✗ 读取 docx 失败: {e}")
        return ""


def extract_pdf_text(file_path: Path) -> str:
    """从 PDF 文件中提取文本"""
    text = ""

    # 方法1: 使用 PyPDF2（纯Python，无需安装额外工具）
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠ PyPDF2 读取失败: {e}")

    # 方法2: 使用 pdfplumber（效果更好）
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠ pdfplumber 读取失败: {e}")

    # 方法3: 使用 pdftotext 命令行工具
    import subprocess
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        result = subprocess.run(
            ['pdftotext', str(file_path), tmp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            import os
            os.unlink(tmp_path)
            return text
        else:
            print(f"  ⚠ pdftotext 失败: {result.stderr}")
    except FileNotFoundError:
        print("  ⚠ 未找到 pdftotext，请安装 poppler-utils")
    except Exception as e:
        print(f"  ⚠ pdftotext 错误: {e}")

    if not text:
        print("  ✗ 无法读取 PDF，请安装 PyPDF2: pip install PyPDF2")
    return text


def extract_docx_text_with_lib(file_path: Path) -> str:
    """从 docx 文件中提取文本（不依赖外部库）"""
    import zipfile
    from xml.etree import ElementTree as ET

    try:
        # docx 是 zip 文件，word/document.xml 包含文本
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_content = z.read('word/document.xml')

        # 解析 XML
        tree = ET.fromstring(xml_content)
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }

        # 提取所有 <w:t> 元素的文本
        paragraphs = []
        current_para = []

        for elem in tree.iter():
            if elem.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t':
                if elem.text:
                    current_para.append(elem.text)
            elif elem.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p':
                if current_para:
                    para_text = ''.join(current_para).strip()
                    if para_text:
                        paragraphs.append(para_text)
                    current_para = []

        # 处理最后一个段落
        if current_para:
            para_text = ''.join(current_para).strip()
            if para_text:
                paragraphs.append(para_text)

        return '\n\n'.join(paragraphs)

    except zipfile.BadZipFile:
        print(f"  ✗ 不是有效的 docx 文件")
        return ""
    except KeyError:
        print(f"  ✗ docx 文件缺少 document.xml")
        return ""
    except Exception as e:
        print(f"  ✗ 读取 docx 失败: {e}")
        return ""


def extract_docx_text_with_lib(file_path: Path) -> str:
    """使用 python-docx 库提取（备用）"""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        return '\n\n'.join(paragraphs)
    except ImportError:
        return ""
    except Exception as e:
        print(f"  ✗ 读取 docx 失败: {e}")
        return ""


def import_text_file(db_path: Path, file_path: Path, category: str = "general") -> int:
    """导入单个文本文件"""
    print(f"导入: {file_path}")

    # 根据文件类型选择读取方式
    suffix = file_path.suffix.lower()

    if suffix == '.docx':
        content = extract_docx_text(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    if not content:
        print("  ⚠ 空文件，跳过")
        return 0

    # 策略1: 如果文件不大(<1000字符)，整体作为一个事实
    if len(content) < 1000:
        tags = f"file:{file_path.stem},imported"
        fact_id = add_fact(db_path, content, category, tags)
        print(f"  ✓ 添加事实 #{fact_id} (完整文件)")
        return 1

    # 策略2: 按段落分割导入
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    count = 0
    for i, para in enumerate(paragraphs):
        if len(para) < 50:  # 跳过太短的段落
            continue
        tags = f"file:{file_path.stem},para:{i},imported"
        fact_id = add_fact(db_path, para[:2000], category, tags)  # 限制长度
        count += 1

    print(f"  ✓ 添加 {count} 个事实")
    return count


def import_directory(db_path: Path, dir_path: Path, pattern: str = "*.md") -> int:
    """导入目录下所有匹配文件"""
    total = 0
    files = list(dir_path.rglob(pattern))
    print(f"找到 {len(files)} 个文件 (模式: {pattern})")

    for file_path in files:
        try:
            count = import_text_file(db_path, file_path)
            total += count
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print(f"\n总计导入: {total} 个事实")
    return total


def import_json(db_path: Path, json_path: Path) -> int:
    """导入 JSON 格式的事实数据"""
    print(f"导入 JSON: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                content = item.get("content", "")
                category = item.get("category", "general")
                tags = item.get("tags", "")
                trust = item.get("trust_score", 0.5)
            else:
                content = str(item)
                category = "general"
                tags = ""
                trust = 0.5

            if content:
                add_fact(db_path, content, category, tags, trust)
                count += 1
    elif isinstance(data, dict):
        # 可能是单条事实或分类组织的数据
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    content = f"{key}: {item}" if not isinstance(item, dict) else item.get("content", str(item))
                    add_fact(db_path, content, key, f"category:{key}")
                    count += 1
            else:
                content = f"{key}: {value}"
                add_fact(db_path, content, "general", f"key:{key}")
                count += 1

    print(f"  ✓ 添加 {count} 个事实")
    return count


def import_memory_files(db_path: Path) -> int:
    """导入现有的 MEMORY.md 和 USER.md"""
    hermes_home = Path.home() / ".hermes"
    total = 0

    for filename in ["MEMORY.md", "USER.md"]:
        file_path = hermes_home / filename
        if file_path.exists():
            print(f"\n导入 {filename}...")
            category = "user" if filename == "USER.md" else "memory"
            count = import_text_file(db_path, file_path, category)
            total += count

    return total


def list_facts(db_path: Path, limit: int = 20):
    """列出已导入的事实"""
    db_path = Path(db_path).expanduser()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, content, category, tags, trust_score, created_at
        FROM facts
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    print(f"\n最近 {len(rows)} 个事实:")
    print("-" * 80)
    for row in rows:
        fact_id, content, category, tags, trust, created = row
        preview = content[:80] + "..." if len(content) > 80 else content
        print(f"#{fact_id} [{category}] (信任度: {trust})")
        print(f"  内容: {preview}")
        if tags:
            print(f"  标签: {tags}")
        print()


def main():
    parser = argparse.ArgumentParser(description="批量导入数据到 Holographic Memory")
    parser.add_argument("--db", type=str, help="数据库路径 (默认从 config 读取)")
    parser.add_argument("--dir", type=str, help="导入目录下所有文件")
    parser.add_argument("--file", type=str, help="导入单个文件")
    parser.add_argument("--json", type=str, help="导入 JSON 文件")
    parser.add_argument("--memory", action="store_true", help="导入现有 MEMORY.md/USER.md")
    parser.add_argument("--pattern", type=str, default="*.md", help="文件匹配模式 (默认: *.md)")
    parser.add_argument("--category", type=str, default="general", help="事实类别")
    parser.add_argument("--list", action="store_true", help="列出已导入的事实")
    parser.add_argument("--init", action="store_true", help="初始化数据库表结构")

    args = parser.parse_args()

    # 获取数据库路径
    db_path = Path(args.db) if args.db else get_db_path()
    db_path = db_path.expanduser()
    print(f"数据库路径: {db_path}")

    # 初始化数据库
    if args.init:
        init_database(db_path)
        return

    # 确保数据库存在
    if not db_path.exists():
        print(f"数据库不存在，创建新数据库...")
        init_database(db_path)

    # 列出事实
    if args.list:
        list_facts(db_path)
        return

    # 导入数据
    total = 0

    if args.memory:
        total += import_memory_files(db_path)

    if args.json:
        total += import_json(db_path, Path(args.json))

    if args.file:
        total += import_text_file(db_path, Path(args.file), args.category)

    if args.dir:
        total += import_directory(db_path, Path(args.dir), args.pattern)

    if total > 0:
        print(f"\n✓ 成功导入 {total} 个事实")
        print(f"\n使用以下方式查看:")
        print(f"  python {sys.argv[0]} --list")
        print(f"\n或在对话中使用: fact_store(action='search', query='关键词')")
    elif not args.list:
        parser.print_help()


if __name__ == "__main__":
    main()
