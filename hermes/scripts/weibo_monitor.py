#!/usr/bin/env python3
"""
微博账号监控脚本 - 监控 @卢麒元 和 @正心以中and修身以和
"""
import requests
import json
import re
import os
import sys
import random
import time
from datetime import datetime

# 添加随机延迟 0-60秒（实现±1分钟打散）
time.sleep(random.randint(0, 60))

# 配置
COOKIES = {
    'WEIBOCN_FROM': '1110006030',
    'SUB': '_2AkMetqkkf8NxqwFRm_sczW7gaIp2zQvEieKo6lj_JRM3HRl-yT9xqkletRB6NTaHyyFIpJ6JE6apHDhzf8Uhhjjn8qn3',
    'SUBP': '0033WrSXqPxfM72-Ws9jqgMF55529P9D9W5JC2ub5M18qb2.NGVB40Ec',
    'MLOGIN': '0',
    '_T_WM': '59815606158',
    'XSRF-TOKEN': '6d1947',
    'mweibo_short_token': '64435e0bd0'
}

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# 监控的账号
ACCOUNTS = {
    '1245732825': '卢麒元',
    '7951175445': '正心以中and修身以和'
}

# 数据存储路径
DATA_DIR = '/home/coordinate35/hermes_data/weibo_data'
STATE_FILE = f'{DATA_DIR}/last_weibo.json'
OUTPUT_FILE = f'{DATA_DIR}/new_weibo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

# 最多记录的已推送微博ID数量
MAX_PUSHED_IDS = 20

def ensure_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_state():
    """加载上次检查状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存检查状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def fetch_weibo(uid, name):
    """获取指定用户的最新微博"""
    url = f'https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&value={uid}&containerid=107603{uid}'
    
    try:
        resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
        data = resp.json()
        
        if data.get('ok') != 1:
            return None, f"API错误: {data.get('msg', 'N/A')}"
        
        cards = data.get('data', {}).get('cards', [])
        weibos = []
        
        for card in cards:
            if card.get('card_type') == 9 and 'mblog' in card:
                m = card['mblog']
                weibo = {
                    'id': str(m.get('id')),
                    'bid': m.get('bid'),
                    'created_at': m.get('created_at'),
                    'source': m.get('source', ''),
                    'text': clean_text(m.get('text', '')),
                    'reposts': m.get('reposts_count', 0),
                    'comments': m.get('comments_count', 0),
                    'attitudes': m.get('attitudes_count', 0),
                    'user': name,
                    'uid': uid
                }
                weibos.append(weibo)
        
        return weibos, None
    except Exception as e:
        return None, str(e)

def parse_weibo_time(time_str):
    """解析微博时间字符串"""
    try:
        # 格式: "Thu Apr 24 12:35:28 +0800 2026"
        return datetime.strptime(time_str, '%a %b %d %H:%M:%S +0800 %Y')
    except:
        return datetime.min

def clean_text(text):
    """清理微博文本"""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&quot;', '"').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('\n', ' ').strip()
    return text

def format_weibo(w):
    """格式化微博输出 - 直接呈现原文，不做加工"""
    lines = []
    lines.append(f"@{w['user']} 发布了新微博")
    lines.append(f"时间: {w['created_at']} | 来源: {w['source']}")
    lines.append("")
    lines.append(w['text'])
    lines.append("")
    lines.append(f"转发 {w['reposts']} | 评论 {w['comments']} | 赞 {w['attitudes']}")
    lines.append("")
    return "\n".join(lines)

def main():
    ensure_dir()
    state = load_state()
    new_weibos = []
    errors = []
    
    # 初始化失败计数器（如果不存在）
    if 'failures' not in state:
        state['failures'] = {}
    
    for uid, name in ACCOUNTS.items():
        weibos, error = fetch_weibo(uid, name)
        
        if error or not weibos:
            # 记录失败
            fail_key = f"{uid}_fail_count"
            state['failures'][fail_key] = state['failures'].get(fail_key, 0) + 1
            fail_count = state['failures'][fail_key]
            
            err_msg = error if error else "未获取到微博"
            
            # 连续3次失败才报告
            if fail_count >= 3:
                errors.append(f"{name}: {err_msg} (连续{fail_count}次失败)")
                # 报告后重置计数器，避免重复报告
                state['failures'][fail_key] = 0
            
            continue
        
        # 成功获取，重置失败计数器
        fail_key = f"{uid}_fail_count"
        if fail_key in state['failures'] and state['failures'][fail_key] > 0:
            state['failures'][fail_key] = 0
        
        # 按时间排序（由新到旧）
        sorted_weibos = sorted(weibos, key=lambda w: parse_weibo_time(w.get('created_at', '')), reverse=True)
        latest_weibo = sorted_weibos[0]
        latest_id = latest_weibo['id']
        latest_time_str = latest_weibo['created_at']
        latest_time = parse_weibo_time(latest_time_str)
        
        # 读取上次记录
        last_id = state.get(uid, {}).get('last_id')
        last_time_str = state.get(uid, {}).get('last_time')
        pushed_ids = state.get(uid, {}).get('pushed_ids', [])  # 已推送的微博ID列表
        
        if last_id and last_time_str:
            # 有上次记录，检查时间比较新的微博
            last_time = parse_weibo_time(last_time_str)
            
            for w in sorted_weibos:
                w_time = parse_weibo_time(w.get('created_at', ''))
                w_id = str(w['id'])
                
                # 检查1：时间是否比上次记录的新
                if w_time > last_time:
                    # 检查2：是否已在推送列表中（防重复）
                    if w_id not in pushed_ids:
                        new_weibos.append(w)
                    else:
                        print(f"[SKIP] {name} 微博 {w_id[:16]}... 已推送过，跳过", file=sys.stderr)
                else:
                    # 由于是按时间倒序，遇到第一个不新的就可以停止了
                    break
        else:
            # 首次运行，记录但不通知
            print(f"[INIT] 首次监控 {name}，记录最新微博ID: {latest_id}, 时间: {latest_time_str}", file=sys.stderr)
        
        # 更新已推送ID列表 - 把本次检测到的所有微博ID都加入，防止API窗口变化导致重复
        account_weibo_ids = [str(w['id']) for w in sorted_weibos]  # 当前API返回的所有微博ID
        account_new_ids = [str(w['id']) for w in new_weibos if w['uid'] == uid]
        
        # 合并：新推送的放前面，已有的放后面，去重
        pushed_ids = account_new_ids + [pid for pid in pushed_ids if pid not in account_new_ids]
        # 再把本次看到的其他微博ID也加入（防止它们下次被误判为"新"的）
        pushed_ids = pushed_ids + [wid for wid in account_weibo_ids if wid not in pushed_ids]
        # 只保留最近 MAX_PUSHED_IDS 个
        pushed_ids = pushed_ids[:MAX_PUSHED_IDS]
        
        # 更新状态（保存最新的ID和时间，防止时间倒退）
        current_last_time = parse_weibo_time(last_time_str) if last_time_str else datetime.min
        
        # 取当前记录和API返回的最新时间中的较大值，防止时间倒退
        if latest_time >= current_last_time:
            # API返回的更新，保存新的
            save_id = latest_id
            save_time = latest_time_str
        else:
            # API可能遗漏了更新的微博，保持原来的记录
            save_id = last_id
            save_time = last_time_str
        
        state[uid] = {
            'last_id': save_id,
            'last_time': save_time,
            'pushed_ids': pushed_ids,  # 已推送的微博ID列表
            'last_check': datetime.now().isoformat(),
            'user': name
        }
    
    # 保存状态
    save_state(state)
    
    # 如果有错误（连续3次失败），输出错误信息
    if errors:
        error_msg = f"⚠️ 微博监控异常 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n" + "\n".join(errors)
        print(error_msg)
        return error_msg
    
    # 如果有新微博，保存并输出
    if new_weibos:
        output = []
        output.append(f"🚀 微博监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"发现 {len(new_weibos)} 条新微博\n")
        
        for w in new_weibos:
            output.append(format_weibo(w))
        
        result = '\n'.join(output)
        
        # 保存到文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(result)
        return result
    
    # 正常运行但无新微博 - 不输出任何内容
    return None

if __name__ == '__main__':
    result = main()
    # Cronjob规则：只看stdout内容，不看退出码
    # - stdout有内容 → 发送消息
    # - stdout为空 → 静默（无论退出码）
    # 所以无新微博时：不print任何内容，exit(0)即可
    sys.exit(0)
