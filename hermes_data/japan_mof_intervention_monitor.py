#!/usr/bin/env python3
"""
日本财务省外汇干预数据自动采集脚本
=====================================
功能:
1. 每日自动拉取日本财务省外汇干预CSV数据
2. 检测是否有新干预记录
3. 保存历史数据到本地
4. 发现新干预时发送通知

数据源: https://www.mof.go.jp/policy/international_policy/reference/feio/foreign_exchange_intervention_operations.csv
作者: Hermes Agent
更新: 2026-05-06
"""

import urllib.request
import ssl
import csv
import json
import hashlib
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

# ============ 配置 ============
DATA_DIR = Path("/home/coordinate35/hermes_data/japan_intervention")
CSV_URL = "https://www.mof.go.jp/policy/international_policy/reference/feio/foreign_exchange_intervention_operations.csv"
HASH_FILE = DATA_DIR / "last_hash.txt"
HISTORY_FILE = DATA_DIR / "intervention_history.json"
LATEST_FILE = DATA_DIR / "latest_intervention.json"
LOG_FILE = DATA_DIR / "monitor.log"

# 上次报告最大记录数
MAX_REPORT_RECORDS = 20

# ============ 初始化目录 ============
DATA_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    """写日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch_csv() -> str:
    """从财务省官网下载CSV数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read().decode("cp932", errors="ignore")


def compute_hash(content: str) -> str:
    """计算内容MD5哈希"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def parse_interventions(csv_content: str) -> list[dict]:
    """解析CSV，提取所有非零干预记录"""
    lines = csv_content.strip().split("\n")
    reader = csv.reader(lines)
    rows = list(reader)

    interventions = []
    current_era = ""
    current_year = ""

    for row in rows[1:]:
        if len(row) < 9:
            continue

        # 更新年号
        if row[0].strip() and "年" in row[0]:
            current_era = row[0].strip()
            era_match = re.search(r"(令和|平成|昭和)(\d+)年", current_era)
            if era_match:
                era_name = era_match.group(1)
                era_num = int(era_match.group(2))
                if era_name == "令和":
                    current_year = str(2018 + era_num)
                elif era_name == "平成":
                    current_year = str(1988 + era_num)
                elif era_name == "昭和":
                    current_year = str(1925 + era_num)

        if row[3].strip() and row[3].strip().isdigit():
            current_year = row[3].strip()

        amount_str = row[6].strip().replace('"', "").replace(",", "")
        if (
            amount_str
            and amount_str != "0"
            and "期計" not in row[0]
            and "期計" not in row[2]
        ):
            try:
                amount = int(amount_str)
                direction = (
                    "阻止日元升值"
                    if "日本円売り" in row[7]
                    else "阻止日元贬值"
                )
                interventions.append(
                    {
                        "era": current_era,
                        "year": int(current_year) if current_year else 0,
                        "month": row[4],
                        "day": row[5],
                        "amount_billion_yen": amount,
                        "amount_trillion_yen": round(amount / 10000, 4),
                        "operation_jp": row[7],
                        "direction": direction,
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except ValueError:
                continue

    return interventions


def load_history() -> list[dict]:
    """加载历史记录"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(records: list[dict]):
    """保存历史记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_last_hash() -> str:
    """加载上次哈希"""
    if HASH_FILE.exists():
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_hash(hash_value: str):
    """保存当前哈希"""
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(hash_value)


def format_intervention(iv: dict) -> str:
    """格式化单条干预记录"""
    amount_t = iv["amount_trillion_yen"]
    direction = iv["direction"]
    date_str = f"{iv['year']}/{iv['month']}/{iv['day']}"
    return f"  {date_str}  {amount_t:.4f}万亿日元  ({direction})"


def generate_report(new_records: list[dict], all_records: list[dict]) -> str:
    """生成彩信报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("🔔 日本财务省外汇干预数据更新通知")
    lines.append(f"   检测时间: {now}")
    lines.append(f"   新增记录: {len(new_records)} 条")
    lines.append("")

    if new_records:
        lines.append("★ 最新干预记录:")
        for iv in new_records:
            lines.append(format_intervention(iv))
        lines.append("")

    # 最近的干预记录 (从全部记录中取最新)
    recent = sorted(all_records, key=lambda x: (x["year"], x["month"], x["day"]), reverse=True)[:MAX_REPORT_RECORDS]

    lines.append(f"📊 最近{len(recent)}次干预历史:")
    for iv in recent:
        lines.append(format_intervention(iv))

    lines.append("")

    # 统计汇总
    buy_yen = [iv for iv in all_records if "贬值" in iv["direction"]]
    sell_yen = [iv for iv in all_records if "升值" in iv["direction"]]

    lines.append("📈 统计汇总:")
    lines.append(f"   总次数: {len(all_records)}")
    lines.append(f"   卖美元/买日元 (阻止贬值): {len(buy_yen)}次, {sum(iv['amount_billion_yen'] for iv in buy_yen):,}亿日元")
    lines.append(f"   买美元/卖日元 (阻止升值): {len(sell_yen)}次, {sum(iv['amount_billion_yen'] for iv in sell_yen):,}亿日元")

    # 最大单笔
    if all_records:
        max_iv = max(all_records, key=lambda x: x["amount_billion_yen"])
        lines.append(f"   历史最大单笔: {max_iv['year']}/{max_iv['month']}/{max_iv['day']}  {max_iv['amount_trillion_yen']:.4f}万亿日元")

    lines.append("")
    lines.append("⚠️ 免责声明: 以上数据来源于日本财务省官方CSV，仅供参考。")

    return "\n".join(lines)


def main():
    """主函数"""
    log("──────────────────────────────────────────")
    log("🚀 日本财务省外汇干预数据监控开始")

    try:
        # 1. 下载CSV
        log("📥 正在下载CSV数据...")
        csv_content = fetch_csv()
        current_hash = compute_hash(csv_content)
        log(f"   CSV大小: {len(csv_content)} 字符")

        # 2. 检查是否有变化
        last_hash = load_last_hash()
        if current_hash == last_hash:
            log("✅ 数据未变化，无新干预记录")
            log("──────────────────────────────────────────")
            return 0

        log("🔄 数据已更新，检测到变化!")

        # 3. 解析干预记录
        log("🔍 解析干预记录...")
        new_records = parse_interventions(csv_content)
        log(f"   解析完成: {len(new_records)} 条记录")

        # 4. 加载历史并对比
        history = load_history()
        existing_keys = {
            (h["year"], h["month"], h["day"], h["amount_billion_yen"]) for h in history
        }

        truly_new = []
        for iv in new_records:
            key = (iv["year"], iv["month"], iv["day"], iv["amount_billion_yen"])
            if key not in existing_keys:
                truly_new.append(iv)
                history.append(iv)

        # 5. 保存
        save_hash(current_hash)
        save_history(history)

        # 保存最新数据JSON
        latest_data = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(history),
            "new_records_today": len(truly_new),
            "latest_interventions": sorted(
                history, key=lambda x: (x["year"], x["month"], x["day"]), reverse=True
            )[:10],
        }
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(latest_data, f, ensure_ascii=False, indent=2)

        # 6. 生成报告
        report = generate_report(truly_new, history)

        if truly_new:
            log(f"🎉 发现 {len(truly_new)} 条新干预记录!")
            for iv in truly_new:
                log(f"   + {iv['year']}/{iv['month']}/{iv['day']}  {iv['amount_trillion_yen']:.4f}万亿日元")
        else:
            log("ℹ️ 数据文件有变化，但未发现新的干预操作")

        # 输出报告到标准输出
        print("\n" + report)

        # 保存报告
        report_file = DATA_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        log(f"📝 报告已保存: {report_file}")

        log("──────────────────────────────────────────")
        return 0

    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        log(traceback.format_exc())
        log("──────────────────────────────────────────")
        return 1


if __name__ == "__main__":
    sys.exit(main())
