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


# ---------- ⚙️ 信号检测（2026-09-28）：供 job 快路径分流；任何异常不得影响主输出 ----------
JOBS_FILE = '/home/coordinate35/.hermes/cron/jobs.json'
LAST_WEIBO_FILE = f'{DATA_DIR}/last_weibo.json'
PROBE_STATE_FILE = f'{DATA_DIR}/probe_state.json'


def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_wb_time(s):
    """微博时间格式：'Mon Sep 28 15:49:53 +0800 2026'（返回本地时区 aware）"""
    try:
        return datetime.strptime(s, '%a %b %d %H:%M:%S +0800 %Y').astimezone()
    except Exception:
        return None


def collect_signals():
    """返回需提示 job 的 SIGNAL 行列表（无信号时为空列表）。"""
    signals = []

    # 信号1：上一轮运行失败 → 可能有未送达帖子，需回补检查（成功后 last_error 自动清空，信号随之消失）
    try:
        jobs = _load_json(JOBS_FILE)
        job_list = jobs.get('jobs', []) if isinstance(jobs, dict) else (jobs or [])
        for j in job_list:
            if not isinstance(j, dict):
                continue
            if j.get('script') == 'weibo_monitor_wrapper.py' or str(j.get('id', '')).startswith('a27ae1b5'):
                err = j.get('last_error')
                streak = j.get('failure_streak') or 0
                if err or streak > 0:
                    detail = str(err)[:100] if err else f'failure_streak={streak}'
                    signals.append(f'⚙️ SIGNAL(回补检查): 上一轮运行失败（{detail}）——请按技能「交付失败与补推恢复」核查故障窗口是否有未送达帖子。')
                break
    except Exception:
        pass

    # 信号2：账号静默 >24h 且静默期内未做探针 → 建议只读实证（12h 阻尼；探针运行后自动停止）
    try:
        lw = _load_json(LAST_WEIBO_FILE) or {}
        ps = _load_json(PROBE_STATE_FILE) or {}
        now = datetime.now().astimezone()
        skip_damping = False
        if ps.get('last_prompt_at'):
            try:
                skip_damping = (now - datetime.fromisoformat(ps['last_prompt_at'])).total_seconds() < 12 * 3600
            except Exception:
                skip_damping = False
        if not skip_damping:
            probe_dt = None
            if ps.get('last_probe_at'):
                try:
                    probe_dt = datetime.fromisoformat(ps['last_probe_at'])
                except Exception:
                    probe_dt = None
            silenced = []
            for uid, st in lw.items():
                if uid == 'failures' or not isinstance(st, dict) or not st.get('last_time'):
                    continue
                lt = _parse_wb_time(st['last_time'])
                if lt is None:
                    continue
                hours = (now - lt).total_seconds() / 3600
                if hours > 24 and (probe_dt is None or probe_dt < lt):
                    silenced.append(f"{st.get('user') or uid}（{hours:.0f}h）")
            if silenced:
                signals.append('⚙️ SIGNAL(静默探针): 账号 ' + '、'.join(silenced) + ' 静默已超24h——请运行 latest_post_probe.py 做一次只读实证（技能「长静默期核验」）。')
                ps['last_prompt_at'] = now.isoformat()
                _save_json(PROBE_STATE_FILE, ps)
    except Exception:
        pass

    return signals


def emit_signals():
    """输出 SIGNAL 行（无信号则无输出）。"""
    try:
        for line in collect_signals():
            print(line)
    except Exception:
        pass

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
            emit_signals()
            return 0
        else:
            # 无内容（无新微博），重置失败计数器，输出 [SILENT] 让 cron job 静默
            reset_failures()
            print("[SILENT]")
            emit_signals()
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
