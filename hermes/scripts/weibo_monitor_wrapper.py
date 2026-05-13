#!/usr/bin/env python3
"""
微博监控包装脚本 - 实现连续3次失败才通知的机制
处理系统级错误（如 Stream stalled、连接超时等）
"""
import subprocess
import json
import os
import sys
from datetime import datetime

# 状态文件路径
DATA_DIR = '/home/coordinate35/hermes_data/weibo_data'
FAILURE_STATE_FILE = f'{DATA_DIR}/cron_failure_state.json'
MAX_FAILURES_BEFORE_NOTIFY = 3

def ensure_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_failure_state():
    """加载失败状态"""
    if os.path.exists(FAILURE_STATE_FILE):
        try:
            with open(FAILURE_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'consecutive_failures': 0, 'last_failure_time': None, 'last_error': None}

def save_failure_state(state):
    """保存失败状态"""
    with open(FAILURE_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def reset_failures():
    """重置失败计数器"""
    save_failure_state({
        'consecutive_failures': 0,
        'last_failure_time': None,
        'last_error': None
    })

def record_failure(error_msg):
    """记录一次失败，返回是否需要通知"""
    state = load_failure_state()
    state['consecutive_failures'] += 1
    state['last_failure_time'] = datetime.now().isoformat()
    state['last_error'] = error_msg[:500]  # 限制长度
    save_failure_state(state)
    
    # 达到3次失败才通知
    return state['consecutive_failures'] >= MAX_FAILURES_BEFORE_NOTIFY

def main():
    ensure_dir()
    
    # 运行实际的监控脚本
    script_path = os.path.join(os.path.dirname(__file__), 'weibo_monitor.py')
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        # 检查是否是系统错误（脚本未完整执行）
        if result.returncode != 0:
            # 脚本错误，记录失败
            error_msg = result.stderr.strip() if result.stderr else "脚本执行异常"
            should_notify = record_failure(error_msg)
            
            if should_notify:
                print(f"""⚠️ 微博监控系统错误 连续3次

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误: {error_msg}

请检查系统状态或网络连接。
""")
                reset_failures()  # 通知后重置
            return 1
        
        # 检查是否有输出内容
        stdout_content = result.stdout.strip()
        
        if stdout_content:
            # 有内容（新微博或错误消息），重置失败计数器并输出
            reset_failures()
            print(stdout_content)
            return 0
        else:
            # 无内容（无新微博），重置失败计数器，输出 [SILENT] 让 cron job 静默
            reset_failures()
            print("[SILENT]")
            return 0
            
    except subprocess.TimeoutExpired:
        # 超时错误
        should_notify = record_failure("脚本执行超时(120秒)")
        if should_notify:
            print(f"""⚠️ 微博监控系统错误 连续3次

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误: 脚本执行超时(120秒)

可能原因：网络连接超时、微博API响应缓慢
""")
            reset_failures()
        return 1
        
    except Exception as e:
        # 其他异常
        should_notify = record_failure(str(e))
        if should_notify:
            print(f"""
26a0️ 微博监控系统错误 连续3次

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
错误: {str(e)}
""")
            reset_failures()
        return 1

if __name__ == '__main__':
    sys.exit(main())
