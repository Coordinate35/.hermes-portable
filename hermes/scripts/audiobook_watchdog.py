#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""听书自动连播看门狗：每分钟检查守护进程，enabled=true 且进程不在则拉起。"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
STATE = Path('/tmp/audiobook_auto_playback.json')
LOG = Path('/tmp/audiobook_auto_advance.log')
DAEMON = HOME / '.hermes/skills/media/audiobook-reader/scripts/auto_advance.py'
PY = '/usr/bin/python3'
DEFAULT_CHAT = 'qqbot:4E42EA828928C02FC47FEB6334392F69'


def log(msg):
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat(timespec="seconds")}] [watchdog] {msg}\n')
    except Exception:
        pass


def pid_is_daemon(pid):
    try:
        os.kill(int(pid), 0)
    except Exception:
        return False
    try:
        cmdline = Path(f'/proc/{int(pid)}/cmdline').read_bytes().decode('utf-8', 'replace')
        return 'auto_advance.py' in cmdline
    except Exception:
        return False


def main():
    try:
        st = json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:
        return
    if not st.get('enabled'):
        return
    pid = st.get('pid')
    if pid and pid_is_daemon(pid):
        return
    book = st.get('book')
    if not book:
        return
    chat = st.get('chat') or DEFAULT_CHAT
    count = str(st.get('count') or 5)
    logf = open(LOG, 'a', encoding='utf-8')
    try:
        subprocess.Popen([PY, str(DAEMON), '--book', book, '--chat', chat, '--count', count],
                         stdout=logf, stderr=logf, start_new_session=True, cwd=str(HOME))
        log(f'守护进程不在（pid={pid}），已重新拉起')
    except Exception as e:
        log(f'拉起失败: {e}')


if __name__ == '__main__':
    main()
