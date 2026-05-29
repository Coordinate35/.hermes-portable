#!/usr/bin/env python3
"""爬 jinyong.net.cn 的三联修订版《射雕英雄传》。

输出: ~/hermes_data/ebooks/_tmp/shediao_sanlian.txt
- 章节标题统一格式: "第一回　XXX" （按 2B 要求还原修订版原书的"回"字格式）
- 正文 40 回放前面，后记 + 附录一/二 放最后（3C 方案）
"""
import re
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request

BASE_URL = 'http://jinyong.net.cn/shediaoyingxiongzhuan/'

# 章节顺序：id 416 = 第1章，依次到 id 455 = 第40章；456=后记 457=附录一 458=附录二
CHAPTERS = []
for i in range(40):
    CHAPTERS.append({'id': 416 + i, 'order': i + 1, 'kind': 'main'})
CHAPTERS.append({'id': 456, 'order': 41, 'kind': 'extra'})  # 后记
CHAPTERS.append({'id': 457, 'order': 42, 'kind': 'extra'})  # 附录一
CHAPTERS.append({'id': 458, 'order': 43, 'kind': 'extra'})  # 附录二

CN_NUMS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
           '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
           '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十',
           '三十一', '三十二', '三十三', '三十四', '三十五', '三十六', '三十七', '三十八', '三十九', '四十']


def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=20) as r:
                # 此站可能是 utf-8 或 gbk，读取 bytes 后用 BeautifulSoup 自动检测
                return r.read()
        except Exception as e:
            print(f'  ⚠️ 第{i+1}次失败 {url}: {e}', file=sys.stderr)
            time.sleep(3)
    raise RuntimeError(f'抓取失败: {url}')


def extract_chapter(html_bytes):
    """提取章节标题和正文。返回 (raw_title, text)。"""
    # BeautifulSoup 自动处理编码
    soup = BeautifulSoup(html_bytes, 'lxml', from_encoding='utf-8')

    # 标题
    title_tag = soup.find('title')
    raw_title = title_tag.get_text(strip=True) if title_tag else ''
    raw_title = re.sub(r'_.*$', '', raw_title).strip()

    # 正文 div id=content
    content_div = soup.find('div', id='content') or soup.find('div', class_='body-content')
    if not content_div:
        return raw_title, ''

    # 删除噪音元素：导航、控件
    for tag in content_div.find_all(['script', 'style', 'a', 'select', 'button', 'input']):
        tag.decompose()

    # 提取所有文本，按 br/段落自然换行
    text = content_div.get_text(separator='\n', strip=True)

    # 拆行清洗
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # 跳过明显的页面噪音
        skip_keywords = [
            '官网：', '选择背景色', '选择字体', '恢复默认', '←上一章', '下一章：',
            '上一章：',
            '黄橙', '洋红', '淡粉', '水蓝', '草绿', '白色',
            '宋体', '黑体', '微软雅黑', '楷体',
            'JinYong.NET', '欢迎收藏', '请记住本站',
            '网友推荐顺序', '版权永归', '本站只做演示', 'Copyright', 'by 金庸',
            '请支持正版', 'admin@jinyong', '铁杆粉丝',
            '一秒钟记住', '记住本站网址', '过目不忘', '拼音全拼写',
            '小说：', '作者：金庸', '小说类型',
        ]
        if any(k in line for k in skip_keywords):
            continue
        # 跳过非常短的、纯标点/特殊符号的行（往往是切分痕迹）
        if len(line) <= 4 and not any(c.isalnum() or '\u4e00' <= c <= '\u9fff' for c in line):
            continue
        # 跳过纯标题重复
        if line == raw_title:
            continue
        lines.append(line)

    # 找正文截断点：以下关键词出现即视为页面噪音区开始
    END_MARKERS = [
        '扩展阅读', '金庸小说的三大版本', '金庸小说有三个版本',
        '版本影视作品', '影视资源', '快捷键',
        '小说阅读顺序', '金庸推荐顺序', '小说历史顺序', '小说创作顺序',
        '版权声明',
    ]
    cut = len(lines)
    for i, line in enumerate(lines):
        if any(m in line for m in END_MARKERS):
            cut = i
            break
    lines = lines[:cut]

    body = '\n\n'.join(lines)
    return raw_title, body


def normalize_main_title(order, raw_title):
    """把"第01章 风雪惊变"还原成"第一回　风雪惊变"。"""
    m = re.match(r'^第\s*\d+\s*章[\s　]*(.+)$', raw_title)
    name = m.group(1).strip() if m else raw_title.strip()
    cn = CN_NUMS[order] if order < len(CN_NUMS) else str(order)
    return f'第{cn}回　{name}'


def main():
    out_dir = Path.home() / 'hermes_data/ebooks/_tmp'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'shediao_sanlian.txt'

    parts = []
    for i, ch in enumerate(CHAPTERS, 1):
        url = f'{BASE_URL}{ch["id"]}.html'
        print(f'[{i}/{len(CHAPTERS)}] id={ch["id"]} ({ch["kind"]})', file=sys.stderr)
        html = fetch(url)
        raw_title, body = extract_chapter(html)
        if not body:
            print(f'  ⚠️ 空内容！raw_title={raw_title!r}', file=sys.stderr)
            continue

        if ch['kind'] == 'main':
            title = normalize_main_title(ch['order'], raw_title)
        else:
            title = raw_title

        parts.append(f'\n\n{title}\n\n{body}\n')
        print(f'  ✓ {title}  ({len(body):,} 字)', file=sys.stderr)
        time.sleep(1.2)

    out_file.write_text(''.join(parts), encoding='utf-8')
    total = sum(len(p) for p in parts)
    print(f'\n✅ 完成。{out_file}  总字数 ~{total:,}', file=sys.stderr)
    print(str(out_file))


if __name__ == '__main__':
    main()
