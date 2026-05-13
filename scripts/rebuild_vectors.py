#!/usr/bin/env python3
"""
重建全息记忆的 HRR 向量
运行时机：import.sh 恢复数据库后自动调用

说明：
  - 该脚本不依赖 Hermes Agent 的包导入机制
  - 通过临时复制 store.py / holographic.py 到无连字符路径，绕开 Python 包名限制
  - 需要 numpy（可选但推荐安装）
"""

import os
import sys
import shutil
import tempfile
import importlib.util

HERMES_HOME = os.path.expanduser("~/.hermes")
DB_PATH = os.path.join(HERMES_HOME, "memory_store.db")
SRC_DIR = os.path.join(HERMES_HOME, "hermes-agent", "plugins", "memory", "holographic")


def load_module_from_path(name: str, path: str):
    """通过 importlib 从任意路径加载单个模块（不需要 __init__.py）"""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    print("[*] HRR 向量重建脚本")

    if not os.path.exists(DB_PATH):
        print(f"[!] 数据库不存在: {DB_PATH}")
        return 1

    # 检查 Hermes Agent 是否已安装
    if not os.path.exists(SRC_DIR):
        print(f"[!] Hermes Agent 未安装，找不到: {SRC_DIR}")
        print("    请先安装 Hermes Agent，再运行此脚本。")
        return 1

    # 检查 numpy
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("[!] 未安装 numpy，正在尝试安装...")
        rc = os.system(f"{sys.executable} -m pip install numpy -q")
        if rc != 0:
            print("[!] numpy 安装失败，请手动安装: pip install numpy")
            return 1

    # 创建临时目录，复制 store.py 和 holographic.py
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_dir = os.path.join(tmpdir, "holo_rebuild")
        os.makedirs(pkg_dir, exist_ok=True)

        required_files = ["store.py", "holographic.py"]
        for fname in required_files:
            src = os.path.join(SRC_DIR, fname)
            dst = os.path.join(pkg_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            else:
                print(f"[!] 缺少必需文件: {src}")
                return 1

        # 通过 importlib 加载这两个模块
        # 先加载 holographic.py（store.py 依赖它）
        holographic_mod = load_module_from_path("holographic_rebuild_hrr", os.path.join(pkg_dir, "holographic.py"))

        # 加载 store.py（内部会 import holographic，我们需要让它能找到）
        sys.modules["holographic"] = holographic_mod
        store_mod = load_module_from_path("holographic_rebuild_store", os.path.join(pkg_dir, "store.py"))

        try:
            print(f"[*] 正在打开数据库: {DB_PATH}")
            store = store_mod.MemoryStore(db_path=DB_PATH)

            print("[*] 正在重建 HRR 向量（可能需要几秒到几分钟）...")
            count = store.rebuild_all_vectors()
            store.close()

            print(f"[+] 成功重建 {count} 条事实的 HRR 向量")
            return 0
        except Exception as e:
            print(f"[!] 重建失败: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(main())
