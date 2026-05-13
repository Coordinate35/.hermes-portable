#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 10 偶发卡顿诊断脚本
运行后会生成报告，关注红色错误和异常延迟
"""

import subprocess
import os
import sys

REPORT_FILE = os.path.expanduser("~/hermes_data/lag_diagnose_report.txt")

def run_cmd(cmd, shell=False):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=shell, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return f"[Error] {e}"

def main():
    lines = []
    lines.append("=" * 60)
    lines.append("Windows 偶发卡顿诊断报告")
    lines.append("=" * 60)

    # 1. 电源计划
    lines.append("\n[1] 当前电源计划")
    lines.append(run_cmd(["powercfg", "/getactivescheme"], shell=False))

    # 2. 磁盘剩余空间
    lines.append("\n[2] 磁盘剩余空间")
    lines.append(run_cmd("wmic logicaldisk get size,freespace,caption", shell=False))

    # 3. 最近24小时的关键错误日志
    lines.append("\n[3] 最近24小时系统错误日志 (Disk / Display / WHEA-Logger)")
    # 使用 wevtutil 查询
    query = (
        'wevtutil qe System /q:"*[System[('
        'TimeCreated[timediff(@SystemTime) <= 86400000]'
        ') and ('
        'Level=1 or Level=2'
        ')]]" /f:text /c:50'
    )
    lines.append(run_cmd(query, shell=True))

    # 4. 应用程序错误（看是否有显卡驱动崩溃）
    lines.append("\n[4] 最近24小时应用程序错误")
    query2 = (
        'wevtutil qe Application /q:"*[System[('
        'TimeCreated[timediff(@SystemTime) <= 86400000]'
        ') and ('
        'Level=1 or Level=2'
        ')]]" /f:text /c:30'
    )
    lines.append(run_cmd(query2, shell=True))

    # 5. 显卡信息
    lines.append("\n[5] 显卡信息")
    lines.append(run_cmd("wmic path win32_videocontroller get name,adapterram,driverversion", shell=False))

    # 6. 硬盘型号
    lines.append("\n[6] 硬盘信息")
    lines.append(run_cmd("wmic diskdrive get model,size,status", shell=False))

    # 7. 近期 Windows Update 历史（看是否有后台偷偷更新）
    lines.append("\n[7] 近期更新历史")
    lines.append(run_cmd("wmic qfe get InstalledOn,HotFixID /format:table", shell=False))

    report = "\n".join(lines)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n\n报告已保存至: {REPORT_FILE}")

if __name__ == "__main__":
    main()
