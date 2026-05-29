"""EPUB 解析器：提取章节标题和正文文本。"""
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import re


def parse_epub(path: str):
    """返回 [{title, text}, ...] 章节列表。"""
    book = epub.read_epub(path, options={'ignore_ncx': True})

    # 优先用 spine 顺序（reading order）
    chapters = []
    seen_ids = set()

    spine_items = []
    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if item and item.get_type() == ITEM_DOCUMENT:
            spine_items.append(item)
            seen_ids.add(item.id)

    # 兜底：spine 之外的 document 也加进来
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        if item.id not in seen_ids:
            spine_items.append(item)

    for item in spine_items:
        html = item.get_content().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'lxml')
        # 清洗噪音
        for tag in soup(['style', 'script', 'nav', 'header', 'footer']):
            tag.decompose()

        # 提取标题：优先 h1/h2/h3，其次 title
        title_tag = soup.find(['h1', 'h2', 'h3'])
        title = title_tag.get_text(strip=True) if title_tag else ''
        if not title:
            t = soup.find('title')
            title = t.get_text(strip=True) if t else item.get_name()

        # 提取正文：所有 p 段落 + 直接文本块，保留段落分隔
        body = soup.find('body') or soup
        paragraphs = []
        for elem in body.find_all(['p', 'div'], recursive=True):
            txt = elem.get_text(separator=' ', strip=True)
            if txt and len(txt) > 1:
                paragraphs.append(txt)

        # 如果上面 p/div 抓不到，退回到 body 全文按 \n 切
        if not paragraphs:
            full = body.get_text(separator='\n', strip=True)
            paragraphs = [p.strip() for p in full.split('\n') if p.strip()]

        # 去重相邻重复段（epub 偶尔会出现）
        dedup = []
        prev = None
        for p in paragraphs:
            if p != prev:
                dedup.append(p)
                prev = p

        text = '\n'.join(dedup).strip()
        if len(text) < 50:  # 跳过封面/版权/空白章
            continue

        chapters.append({'title': title, 'text': text})

    # 如果整本只有 1 章但很大，可能 spine 没正确切分，按内部章节标题再切
    if len(chapters) == 1 and len(chapters[0]['text']) > 50000:
        from .common import is_chapter_title
        lines = chapters[0]['text'].split('\n')
        split_chapters = []
        cur_title = chapters[0]['title']
        cur_buf = []
        for line in lines:
            if is_chapter_title(line):
                if cur_buf:
                    split_chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})
                cur_title = line.strip()
                cur_buf = []
            else:
                cur_buf.append(line)
        if cur_buf:
            split_chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})
        if len(split_chapters) > 1:
            chapters = split_chapters

    return chapters
