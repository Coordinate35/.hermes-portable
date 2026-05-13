#!/usr/bin/env python3
"""
加密记账核心模块
- AES-256-GCM 逐行加密
- 按年切割文件: expenses_YYYY.jsonl.enc
- 密钥独立存放: ~/.hermes/secrets/accounting.key
"""
import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ------------- 路径配置 -------------
HOME = Path.home()
DATA_DIR = HOME / "hermes_data" / "accounting"
KEY_PATH = HOME / ".hermes" / "secrets" / "accounting.key"

# ------------- 分类体系 -------------
CATEGORIES = {
    "刚性": ["食", "住", "行", "医"],
    "娱乐": ["餐饮娱乐", "休闲", "购物"],
    "成长": ["学习", "健康", "工具"],
    "其他": ["人情", "杂项"],
}


# ------------- 密钥管理 -------------
def load_or_create_key() -> bytes:
    """加载或生成 256-bit AES 密钥"""
    if KEY_PATH.exists():
        return base64.b64decode(KEY_PATH.read_bytes())

    KEY_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = AESGCM.generate_key(bit_length=256)
    KEY_PATH.write_bytes(base64.b64encode(key))
    KEY_PATH.chmod(0o600)
    return key


# ------------- 加解密 -------------
def encrypt_line(plaintext: str, key: bytes) -> str:
    """加密单行数据，返回 base64(nonce + ciphertext)"""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_line(encoded: str, key: bytes) -> str:
    """解密单行数据"""
    raw = base64.b64decode(encoded)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


# ------------- 文件操作 -------------
def get_file_for_year(year: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"expenses_{year}.jsonl.enc"


def append_record(record: dict, key: bytes):
    """追加一条加密记录"""
    year = datetime.fromisoformat(record["timestamp"]).year
    file_path = get_file_for_year(year)
    line = encrypt_line(json.dumps(record, ensure_ascii=False), key)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_all_records(year: int = None, key: bytes = None) -> list:
    """读取并解密记录"""
    if not DATA_DIR.exists():
        return []
    files = sorted(DATA_DIR.glob("expenses_*.jsonl.enc"))
    if year:
        files = [f for f in files if f.name == f"expenses_{year}.jsonl.enc"]

    records = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(decrypt_line(line, key))
                    records.append(rec)
                except Exception as e:
                    print(f"[!] 解密失败 {fp.name}: {e}", file=sys.stderr)
    return records


def rewrite_year_file(year: int, records: list, key: bytes):
    """重写整个年度文件（用于删除操作）"""
    file_path = get_file_for_year(year)
    tmp = file_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for rec in records:
            line = encrypt_line(json.dumps(rec, ensure_ascii=False), key)
            f.write(line + "\n")
    tmp.replace(file_path)


# ------------- 业务逻辑 -------------
def parse_when(when: str) -> datetime:
    """灵活解析时间字符串，返回 datetime。
    支持：
    - 完整 ISO: 2026-05-13T12:30:00 / 2026-05-13 12:30:00
    - 仅日期: 2026-05-13 (默认补 12:00:00)
    - 仅日期月日: 05-13 / 5-13 (用当前年份)
    - 中文相对: 今天/昨天/前天 [+ HH:MM]
    - 时间词: 早上/上午/中午/下午/晚上 (映射到 8/10/12/15/20 点)
    """
    if not when:
        return datetime.now()

    s = when.strip()
    now = datetime.now()

    # 中文时段 → 小时
    period_map = {
        "凌晨": 3, "早上": 8, "早晨": 8, "上午": 10, "中午": 12,
        "下午": 15, "傍晚": 18, "晚上": 20, "夜里": 22, "深夜": 23,
    }

    # 1. 处理"今天/昨天/前天/X天前"前缀
    base_date = None
    for prefix, delta in [("今天", 0), ("昨天", -1), ("前天", -2),
                          ("大前天", -3)]:
        if s.startswith(prefix):
            base_date = (now + timedelta(days=delta)).date()
            s = s[len(prefix):].strip()
            break

    if base_date is None:
        import re
        m = re.match(r"(\d+)\s*天前", s)
        if m:
            base_date = (now - timedelta(days=int(m.group(1)))).date()
            s = s[m.end():].strip()

    # 2. 处理时段词
    hour_from_period = None
    for word, h in period_map.items():
        if word in s:
            hour_from_period = h
            s = s.replace(word, "").strip()
            break

    # 3. 如果有时段前缀，尝试拼接小时分钟
    if base_date is not None:
        # 如果剩下的 s 形如 "14:30" 或 "14点30" 或 "14"
        import re
        hh, mm = None, 0
        m = re.match(r"^(\d{1,2})[:点](\d{1,2})?分?$", s)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2)) if m.group(2) else 0
        elif re.match(r"^\d{1,2}$", s):
            hh = int(s)
        elif s == "":
            hh = hour_from_period if hour_from_period is not None else 12
        else:
            raise ValueError(f"无法解析时间剩余部分: '{s}'")
        if hh is None:
            hh = hour_from_period if hour_from_period is not None else 12
        # 如果用户同时提供了时段词（下午/晚上等）和具体小时数，
        # 且小时 < 12，把时段词作为 AM/PM 提示进行修正
        if hour_from_period is not None and hh is not None and hh < 12:
            if hour_from_period >= 12 and hh < 12:
                hh += 12  # 下午3点 → 15
            elif hour_from_period < 12 and hh == 12:
                hh = 0    # 早上12点 → 00
        return datetime.combine(base_date, datetime.min.time()).replace(
            hour=hh, minute=mm, second=0
        )

    # 4. 尝试标准 ISO 解析
    try:
        # 兼容 "YYYY-MM-DD HH:MM:SS" 和 "YYYY-MM-DDTHH:MM:SS"
        s2 = s.replace(" ", "T")
        dt = datetime.fromisoformat(s2)
        # 如果是纯日期（解析后时分秒都为 0），默认补成中午 12:00
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and "T" not in s2:
            dt = dt.replace(hour=12)
        return dt
    except ValueError:
        pass

    # 5. 仅日期 YYYY-MM-DD
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        h = hour_from_period if hour_from_period is not None else 12
        return d.replace(hour=h)
    except ValueError:
        pass

    # 6. 月-日 (本年)
    try:
        d = datetime.strptime(s, "%m-%d").replace(year=now.year)
        h = hour_from_period if hour_from_period is not None else 12
        return d.replace(hour=h)
    except ValueError:
        pass

    raise ValueError(f"无法解析时间: '{when}'")


def add_expense(amount: float, description: str, category: str,
                subcategory: str, note: str = "", when: str = None) -> dict:
    """新增一笔支出。when 可指定历史时间（见 parse_when）"""
    key = load_or_create_key()
    ts = parse_when(when) if when else datetime.now()
    # 生成唯一 ID（基于时间戳，但加上当前微秒避免冲突）
    micro = datetime.now().microsecond
    rec_id = ts.strftime("%Y%m%d%H%M%S") + f"{int(micro/1000):03d}"
    record = {
        "id": rec_id,
        "timestamp": ts.isoformat(timespec="seconds"),
        "amount": round(float(amount), 2),
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "note": note,
    }
    append_record(record, key)
    return record


def delete_expense(rec_id: str) -> tuple:
    """根据 ID 删除一笔，返回 (被删记录, 是否成功)"""
    key = load_or_create_key()
    year = int(rec_id[:4])
    records = read_all_records(year=year, key=key)
    target = None
    remaining = []
    for r in records:
        if r["id"] == rec_id:
            target = r
        else:
            remaining.append(r)
    if not target:
        return None, False
    rewrite_year_file(year, remaining, key)
    return target, True


def find_expense(query: str = None, last_n: int = 10) -> list:
    """查找/列出最近的支出"""
    key = load_or_create_key()
    records = read_all_records(key=key)
    records.sort(key=lambda r: r["timestamp"], reverse=True)
    if query:
        q = query.lower()
        records = [r for r in records
                   if q in r.get("description", "").lower()
                   or q in r.get("note", "").lower()
                   or q in r.get("subcategory", "").lower()]
    return records[:last_n]


def summarize(start: datetime, end: datetime) -> dict:
    """按时间范围汇总"""
    key = load_or_create_key()
    all_records = read_all_records(key=key)
    in_range = [r for r in all_records
                if start <= datetime.fromisoformat(r["timestamp"]) < end]

    by_category = defaultdict(lambda: {"total": 0.0, "count": 0,
                                        "subcategories": defaultdict(float)})
    total = 0.0
    for r in in_range:
        cat = r["category"]
        sub = r["subcategory"]
        amt = r["amount"]
        by_category[cat]["total"] += amt
        by_category[cat]["count"] += 1
        by_category[cat]["subcategories"][sub] += amt
        total += amt

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total": round(total, 2),
        "count": len(in_range),
        "by_category": {k: {"total": round(v["total"], 2),
                            "count": v["count"],
                            "subcategories": {s: round(a, 2)
                                              for s, a in v["subcategories"].items()}}
                        for k, v in by_category.items()},
        "records": in_range,
    }


# ------------- CLI -------------
def cli():
    parser = argparse.ArgumentParser(description="Encrypted accounting tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add an expense")
    p_add.add_argument("--amount", type=float, required=True)
    p_add.add_argument("--desc", required=True)
    p_add.add_argument("--cat", required=True)
    p_add.add_argument("--sub", required=True)
    p_add.add_argument("--note", default="")
    p_add.add_argument("--when", default=None,
                       help="时间，支持 '昨天 14:00' / '2026-05-13' / '前天下午' 等")

    p_del = sub.add_parser("delete", help="delete an expense by id")
    p_del.add_argument("--id", required=True)

    p_find = sub.add_parser("find", help="find recent expenses")
    p_find.add_argument("--query", default=None)
    p_find.add_argument("--n", type=int, default=10)

    p_sum = sub.add_parser("summary", help="summarize expenses")
    p_sum.add_argument("--start", required=True, help="YYYY-MM-DD")
    p_sum.add_argument("--end", required=True, help="YYYY-MM-DD (exclusive)")

    sub.add_parser("init", help="initialize key and dirs")

    args = parser.parse_args()

    if args.cmd == "init":
        load_or_create_key()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"OK key={KEY_PATH} data={DATA_DIR}")

    elif args.cmd == "add":
        rec = add_expense(args.amount, args.desc, args.cat, args.sub,
                          args.note, when=args.when)
        print(json.dumps(rec, ensure_ascii=False, indent=2))

    elif args.cmd == "delete":
        rec, ok = delete_expense(args.id)
        if not ok:
            print(f"NOT_FOUND {args.id}")
            sys.exit(1)
        print(json.dumps({"deleted": rec}, ensure_ascii=False, indent=2))

    elif args.cmd == "find":
        records = find_expense(args.query, args.n)
        print(json.dumps(records, ensure_ascii=False, indent=2))

    elif args.cmd == "summary":
        start = datetime.fromisoformat(args.start)
        end = datetime.fromisoformat(args.end)
        result = summarize(start, end)
        # 不输出 records 的明细，避免控制台太长
        result_compact = {k: v for k, v in result.items() if k != "records"}
        result_compact["record_ids"] = [r["id"] for r in result["records"]]
        print(json.dumps(result_compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
