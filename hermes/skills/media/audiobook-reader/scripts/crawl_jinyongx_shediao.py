#!/usr/bin/env python3
"""爬 jinyongx.com/she/ 的三联修订版射雕英雄传。

输出: ~/hermes_data/ebooks/_tmp/shediao_sanlian.txt
- 章节标题统一格式: "第一回　XXX" （还原修订版原书格式）
- 正文 40 回放前面，附录/后记放最后
"""
import re
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request

# 章节顺序：正文 1-40 (id 201→162)，然后后记、附录一、附录二
CHAPTERS = []
# 正文 40 回：id 201 是第1章，id 162 是第40章
for i in range(40):
    page_id = 201 - i
    chapter_num = i + 1
    CHAPTERS.append({'id': page_id, 'order': chapter_num, 'kind': 'main'})
# 后记、附录
CHAPTERS.append({'id': 161, 'order': 41, 'kind': 'extra', 'fallback_title': '后记'})
CHAPTERS.append({'id': 160, 'order': 42, 'kind': 'extra', 'fallback_title': '附录一　成吉思汗家族'})
CHAPTERS.append({'id': 159, 'order': 43, 'kind': 'extra', 'fallback_title': '附录二　关于“全真教”'})

# 数字转中文
CN_NUMS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
           '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
           '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十',
           '三十一', '三十二', '三十三', '三十四', '三十五', '三十六', '三十七', '三十八', '三十九', '四十']


def fetch(url, retries=3):
    """带重试的 GET。"""
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode('utf-8', errors='replace')
        except Exception as e:
            print(f'  ⚠️ 第{i+1}次失败 {url}: {e}', file=sys.stderr)
            time.sleep(3)
    raise RuntimeError(f'抓取失败: {url}')


def extract_chapter(html, kind='main'):
    """提取章节标题和正文。返回 (title, text)。"""
    soup = BeautifulSoup(html, 'lxml')

    # 标题：<title>第40章　华山论剑_射雕英雄传修订版_金庸网</title>
    title_tag = soup.find('title')
    raw_title = title_tag.get_text(strip=True) if title_tag else ''
    # 去掉站方后缀
    title = re.sub(r'_射雕.*$', '', raw_title).strip()

    # 正文：找 class 含 vertical / vcon 的 div
    content_div = (soup.find('div', class_='vertical') or
                   soup.find('div', class_='vcon'))
    if not content_div:
        # 兜底：找最长的 div
        divs = sorted(soup.find_all('div'), key=lambda d: len(d.get_text()), reverse=True)
        content_div = divs[0] if divs else soup

    # 清洗噪音
    for tag in content_div(['script', 'style', 'a', 'div']):
        # 注意：内层 div 大多是广告/导航，但有些站把段落放 div 里，需要看实际情况
        # 这里先把 a/script/style 干掉，div 不动
        if tag.name in ('script', 'style', 'a'):
            tag.decompose()

    # 提取文本，按 p / br 分段
    paragraphs = []
    for p in content_div.find_all('p'):
        text = p.get_text(separator=' ', strip=True)
        if text and len(text) > 1:
            paragraphs.append(text)

    if not paragraphs:
        # 退回到 br 分段
        full = content_div.get_text(separator='\n', strip=True)
        paragraphs = [l.strip() for l in full.split('\n') if l.strip()]

    # 第一段往往就是标题（如"关于"全真教""），跳过和 title 重复的段
    if paragraphs:
        first = re.sub(r'[\s　]+', '', paragraphs[0])
        norm_title = re.sub(r'[\s　]+', '', title)
        if first.startswith(norm_title) or norm_title.startswith(first):
            paragraphs[0] = paragraphs[0].replace(title.replace(' ', ''), '', 1).strip()
            if not paragraphs[0]:
                paragraphs = paragraphs[1:]

    text = '\n\n'.join(p for p in paragraphs if p)
    return title, text


def normalize_main_title(order, raw_title):
    """把"第40章　华山论剑"还原成"第四十回　华山论剑"。"""
    # 提取章名（去掉"第X章"前缀）
    m = re.match(r'^第\s*\d+\s*章[\s　]*(.+)$', raw_title)
    name = m.group(1).strip() if m else raw_title
    cn = CN_NUMS[order] if order < len(CN_NUMS) else str(order)
    return f'第{cn}回　{name}'


def main():
    out_dir = Path.home() / 'hermes_data/ebooks/_tmp'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'shediao_sanlian.txt'

    all_text = []
    for i, ch in enumerate(CHAPTERS, 1):
        url = f'https://jinyongx.com/she/{ch["id"]}.html'
        print(f'[{i}/{len(CHAPTERS)}] {url}', file=sys.stderr)
        html = fetch(url)
        raw_title, text = extract_chapter(html, ch['kind'])

        if ch['kind'] == 'main':
            title = normalize_main_title(ch['order'], raw_title)
        else:
            # 后记/附录用站方标题，但删掉序号
            title = raw_title

        all_text.append(f'\n\n{title}\n\n{text}\n')
        print(f'    ✓ {title}  ({len(text)} 字)', file=sys.stderr)
        time.sleep(1.5)  # 礼貌延迟

    out_file.write_text(''.join(all_text), encoding='utf-8')
    total = sum(len(t) for t in all_text)
    print(f'\n✅ 完成。{out_file}  总字数 ~{total:,}', file=sys.stderr)
    print(str(out_file))


if __name__ == '__main__':
    main()
