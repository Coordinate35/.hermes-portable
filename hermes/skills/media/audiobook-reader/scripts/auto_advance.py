#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""听书自动连播守护进程。

用法:
  python3 auto_advance.py --book "<书名>" [--chat qqbot:<id>] [--count 5] [--buffer 2]
  python3 auto_advance.py --stop
  python3 auto_advance.py --status

行为:
  1. read.py --mode continue 取段并推进进度
  2. 拼接文本（过滤章末署名噪音），合成 combined wav（命中缓存跳过）
  3. hermes send 独立发 MEDIA 消息
  4. ffprobe 测时长 → 可中断 sleep(时长+缓冲) → 下一段
  5. 每 2 秒检查 auto_playback.json 的 enabled，false 即退出

状态文件: ~/hermes_data/ebooks/auto_playback.json
日志:     ~/hermes_data/ebooks/auto_advance.log
"""
import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
EBOOKS = HOME / 'hermes_data' / 'ebooks'
STATE = Path('/tmp/audiobook_auto_playback.json')
LOCK = Path('/tmp/audiobook_auto_advance.lock')
LOG = Path('/tmp/audiobook_auto_advance.log')
PRECOMPOSE_LOG = Path('/tmp/audiobook_precompose.log')
SKILL_SCRIPTS = HOME / '.hermes/skills/media/audiobook-reader/scripts'
READ_PY = SKILL_SCRIPTS / 'read.py'
PRECOMPOSE_PY = SKILL_SCRIPTS / 'precompose.py'
VENV_PY = HOME / 'hermes_data/ebooks/.venv/bin/python'
WIN_TTS = HOME / '.hermes/scripts/win_tts.sh'
MELO_DIR = HOME / 'hermes_data/melotts'
HERMES = HOME / '.local/bin/hermes'
DEFAULT_CHAT = 'qqbot:4E42EA828928C02FC47FEB6334392F69'
NOISE_TEXTS = {'金庸'}
TTS_MAX_CHARS = 2400

_stop = False


def now():
    return datetime.now().isoformat(timespec='seconds')


def log(msg):
    line = f"[{now()}] {msg}"
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def read_state():
    try:
        return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def patch_state(**kw):
    st = read_state()
    st.update(kw)
    st['updated_at'] = now()
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, STATE)


def run(cmd, timeout, env=None, capture=True):
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, env=env)
        return r.returncode, (r.stdout or ''), (r.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, '', 'timeout'
    except Exception as e:
        return 125, '', str(e)


def get_batch(book, count):
    rc, out, err = run([str(VENV_PY), str(READ_PY), '--book', book,
                        '--mode', 'continue', '--count', str(count)], 120)
    if rc != 0:
        raise RuntimeError(f'read.py failed rc={rc} err={err[:300]}')
    return json.loads(out)


def synth_win_tts(text, out_path):
    env = dict(os.environ)
    env['WIN_TTS_MAX_TIME'] = '600'
    rc, out, err = run(['bash', str(WIN_TTS), text, str(out_path)], 900, env=env)
    ok = rc == 0 and out_path.exists() and out_path.stat().st_size > 10240
    if not ok:
        log(f'win_tts fail rc={rc} err={err[:200]}')
    return ok


def synth_melotts(text, out_path):
    melo_py = MELO_DIR / '.venv/bin/python'
    melo_script = MELO_DIR / 'melo_tts.py'
    if not (melo_py.exists() and melo_script.exists()):
        return False
    rc, out, err = run([str(melo_py), str(melo_script), text, str(out_path)], 900)
    ok = rc == 0 and out_path.exists() and out_path.stat().st_size > 10240
    if not ok:
        log(f'melotts fail rc={rc} err={err[:200]}')
    return ok


def synth_edge(text, out_path):
    mp3 = out_path.with_suffix('.mp3')
    rc, out, err = run(['edge-tts', '--text', text, '--voice', 'zh-CN-XiaoxiaoNeural',
                        '--write-media', str(mp3)], 600)
    if rc != 0 or not mp3.exists() or mp3.stat().st_size <= 10240:
        log(f'edge-tts fail rc={rc} err={err[:200]}')
        return False
    rc2, _, err2 = run(['ffmpeg', '-y', '-i', str(mp3), str(out_path)], 300)
    if rc2 != 0 or not out_path.exists() or out_path.stat().st_size <= 10240:
        log(f'ffmpeg convert fail rc={rc2} err={err2[:200]}')
        return False
    return True


def synth(text, out_path):
    if synth_win_tts(text, out_path):
        return True
    log('降级到 MeloTTS')
    if synth_melotts(text, out_path):
        return True
    log('降级到 edge-tts')
    return synth_edge(text, out_path)


def split_text(text, limit=TTS_MAX_CHARS):
    parts, cur = [], ''
    for sent in re.split(r'(?<=[。！？\n])', text):
        if not sent:
            continue
        if len(cur) + len(sent) > limit and cur:
            parts.append(cur)
            cur = sent
        else:
            cur += sent
    if cur:
        parts.append(cur)
    return parts


def synth_long(text, out_path):
    if len(text) <= TTS_MAX_CHARS:
        return synth(text, out_path)
    chunks = split_text(text)
    log(f'长文本 {len(text)} 字，分 {len(chunks)} 段合成')
    segs = []
    for i, chunk in enumerate(chunks):
        seg = out_path.with_name(f'{out_path.stem}_seg{i:03d}.wav')
        if not (seg.exists() and seg.stat().st_size > 10240):
            if not synth(chunk, seg):
                return False
        segs.append(seg)
    lst = out_path.with_suffix('.concat.txt')
    lst.write_text(''.join(f"file '{p}'\n" for p in segs), encoding='utf-8')
    rc, _, err = run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
                      '-acodec', 'pcm_s16le', str(out_path)], 600)
    if rc != 0 or not out_path.exists() or out_path.stat().st_size <= 10240:
        log(f'concat fail rc={rc} err={err[:200]}')
        return False
    return True


def audio_duration(path):
    rc, out, _ = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'default=nw=1:nk=1', str(path)], 60)
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def notify(chat, text):
    run([str(HERMES), 'send', '--to', chat, text], 120)


def send_media(chat, path):
    for attempt in range(3):
        rc, out, err = run([str(HERMES), 'send', '--to', chat, f'MEDIA:{path}'], 300)
        if rc == 0:
            return True
        log(f'send fail attempt={attempt+1} rc={rc} err={err[:200]}')
        time.sleep(5)
    return False


def start_precompose(book, count):
    try:
        lf = open(PRECOMPOSE_LOG, 'a', encoding='utf-8')
        subprocess.Popen([str(VENV_PY), str(PRECOMPOSE_PY), '--book', book,
                          '--peek-offset', '0', '--count', str(count)],
                         stdout=lf, stderr=lf, start_new_session=True)
        log('已启动下一批预合成')
    except Exception as e:
        log(f'precompose 启动失败: {e}')


def do_stop():
    st = read_state()
    st['enabled'] = False
    st['updated_at'] = now()
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, STATE)
    pid = st.get('pid')
    killed = False
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
            killed = True
        except Exception:
            pass
    print(json.dumps({'stopped': True, 'pid': pid, 'killed': killed}, ensure_ascii=False))


def do_status():
    st = read_state()
    pid = st.get('pid')
    alive = False
    if pid:
        try:
            os.kill(int(pid), 0)
            alive = True
        except Exception:
            alive = False
    print(json.dumps({'state': st, 'pid_alive': alive}, ensure_ascii=False, indent=2))


def on_signal(signum, frame):
    global _stop
    _stop = True
    log(f'收到信号 {signum}，准备退出')


def main():
    global _stop
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', default=None)
    ap.add_argument('--chat', default=None)
    ap.add_argument('--count', type=int, default=None)
    ap.add_argument('--buffer', type=float, default=2.0)
    ap.add_argument('--stop', action='store_true')
    ap.add_argument('--status', action='store_true')
    args = ap.parse_args()

    if args.stop:
        do_stop()
        return
    if args.status:
        do_status()
        return

    st = read_state()
    book = args.book or st.get('book')
    if not book:
        print('缺少 --book', file=sys.stderr)
        sys.exit(2)
    chat = args.chat or st.get('chat') or DEFAULT_CHAT
    count = args.count or int(st.get('count') or 5)
    buffer_s = args.buffer if args.buffer is not None else float(st.get('buffer_s') or 2.0)

    EBOOKS.mkdir(parents=True, exist_ok=True)
    lock_fh = open(LOCK, 'w')
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('已有实例在运行', file=sys.stderr)
        sys.exit(3)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    if LOG.exists() and LOG.stat().st_size > 2 * 1024 * 1024:
        try:
            os.replace(LOG, LOG.with_name(LOG.name + '.1'))
        except Exception:
            pass

    patch_state(enabled=True, book=book, chat=chat, count=count,
                buffer_s=buffer_s, pid=os.getpid(), started_at=now(), last_error=None)
    log(f'守护进程启动 book={book} chat={chat} count={count} pid={os.getpid()}')

    failures = 0
    while not _stop:
        cur = read_state()
        if not cur.get('enabled'):
            log('enabled=false，退出')
            break
        try:
            data = get_batch(book, count)
        except Exception as e:
            log(f'取段失败: {e}')
            failures += 1
            if failures >= 3:
                patch_state(enabled=False, last_error=str(e))
                notify(chat, f'自动连播停止：取段连续失败（{e}）')
                break
            time.sleep(10)
            continue

        paras = [p for p in data.get('paragraphs', [])
                 if not (len(p['text'].strip()) < 10 and p['text'].strip() in NOISE_TEXTS)]
        if not paras:
            if data.get('is_book_end'):
                patch_state(enabled=False)
                notify(chat, '自动连播结束：全书已读完。')
                break
            time.sleep(2)
            continue

        chapter = data['chapter']
        first_idx = paras[0]['index']
        last_idx = paras[-1]['index']
        cache_dir = Path(data['audio_cache_dir'])
        cache_dir.mkdir(parents=True, exist_ok=True)
        out_path = cache_dir / f'combined_ch{chapter:03d}_p{first_idx:03d}-p{last_idx:03d}.wav'

        if out_path.exists() and out_path.stat().st_size > 10240:
            log(f'缓存命中 {out_path.name}')
        else:
            text = '\n\n'.join(p['text'] for p in paras)
            log(f'合成 ch{chapter} p{first_idx}-{last_idx} ({len(text)} 字)')
            if not synth_long(text, out_path):
                failures += 1
                log('合成失败一次')
                if failures >= 3:
                    patch_state(enabled=False, last_error='TTS 连续失败')
                    notify(chat, '自动连播停止：语音合成连续失败三次。')
                    break
                time.sleep(10)
                continue

        dur = audio_duration(out_path)
        if not send_media(chat, out_path):
            patch_state(enabled=False, last_error='send failed')
            log('发送连续失败，退出')
            break
        failures = 0
        patch_state(last_delivered={'chapter': chapter, 'range': [first_idx, last_idx],
                                    'audio': str(out_path), 'duration_s': round(dur, 1),
                                    'sent_at': now()})
        log(f'已发送 {out_path.name} 时长={dur:.1f}s')

        if data.get('is_book_end'):
            patch_state(enabled=False)
            notify(chat, '自动连播结束：全书已读完。')
            break

        start_precompose(book, count)

        deadline = time.time() + max(dur, 1.0) + buffer_s
        while time.time() < deadline and not _stop:
            if not read_state().get('enabled'):
                _stop = True
                break
            time.sleep(2)

    patch_state(pid=None)
    log('守护进程退出')


if __name__ == '__main__':
    main()
