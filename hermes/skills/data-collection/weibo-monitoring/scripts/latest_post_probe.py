#!/usr/bin/env python3
"""长静默期只读核验探针 —— weibo-monitoring skill 附属脚本（2026-09-28）。

用途：常态日更账号静默 >24h 时，实证"真静默"还是"管线漏抓"。
原则：只读——不写任何状态文件、不运行监控脚本；仅 2 次 getIndex 抓取。
做法：取各账号卡片 mblog 的 created_at 最大值，与 last_weibo.json 的 last_time 比对：
      相等 → 真静默（照常回 [SILENT]）；探针更大 → 可能漏抓，按 skill 恢复流程处理。
用法（勿用 python3 -c 内联，会挂起）：
      timeout 90 python3 ~/.hermes/skills/data-collection/weibo-monitoring/scripts/latest_post_probe.py
"""
import ast
import json
import re
import sys
from datetime import datetime

import requests

MONITOR_SRC = '/home/coordinate35/.hermes/scripts/weibo_monitor.py'
STATE_FILE = '/home/coordinate35/hermes_data/weibo_data/last_weibo.json'
ACCOUNTS = {'1245732825': '卢麒元', '7951175445': '正心以中and修身以和'}
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}


def load_cookies():
    src = open(MONITOR_SRC, encoding='utf-8').read()
    m = re.search(r"COOKIES\s*=\s*(\{.*?\})", src, re.S)
    if not m:
        sys.exit('无法从 weibo_monitor.py 提取 COOKIES，请检查源文件')
    return ast.literal_eval(m.group(1))


def parse_t(s):
    try:
        return datetime.strptime(s, '%a %b %d %H:%M:%S +0800 %Y')
    except Exception:
        return datetime.min


def main():
    cookies = load_cookies()
    try:
        state = json.load(open(STATE_FILE, encoding='utf-8'))
    except Exception as e:
        state = {}
        print(f'（读状态文件失败：{e}；仅输出探针所见）')
    print('NOW:', datetime.now().isoformat())
    for uid, name in ACCOUNTS.items():
        url = (f'https://m.weibo.cn/api/container/getIndex?uid={uid}'
               f'&type=uid&value={uid}&containerid=107603{uid}')
        try:
            d = requests.get(url, headers=HEADERS, cookies=cookies, timeout=15).json()
            cards = d.get('data', {}).get('cards', [])
            mbs = [c['mblog'] for c in cards if c.get('card_type') == 9 and 'mblog' in c]
            print(f'=== {name} ({uid}) ok={d.get("ok")} mblogs={len(mbs)}')
            if not mbs:
                print('  ⚠️ 空列表（监控脚本会把此计为一次失败）')
                continue
            ordered = sorted(mbs, key=lambda m: parse_t(m.get('created_at', '')), reverse=True)
            top = ordered[0]
            print(f'  探针最新: {top.get("id")} | {top.get("created_at")} | {(top.get("text") or "")[:45]}')
            st = state.get(uid, {})
            print(f'  状态记录: {st.get("last_id")} | {st.get("last_time")}')
            same = parse_t(top.get('created_at', '')) == parse_t(st.get('last_time') or '')
            print(f'  结论: {"一致 —— 真静默" if same else "⚠️ 不一致 —— 探针所见更新，需排查是否漏抓"}')
        except Exception as e:
            print(f'=== {name} ({uid}) EXCEPTION: {e}')


if __name__ == '__main__':
    main()
