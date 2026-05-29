"""MOBI 解析器：用 mobi 库解包成 epub/html，再走 epub 解析器。"""
import os
import shutil
import tempfile
import mobi as mobi_lib
from .epub_parser import parse_epub


def parse_mobi(path: str):
    """mobi.extract() 会解包成临时目录，里面通常含 epub 或 html。"""
    tempdir, filepath = mobi_lib.extract(path)
    try:
        # mobi 库通常解包出 .epub 或 .html
        if filepath.lower().endswith('.epub'):
            return parse_epub(filepath)
        # 若是 html，找解包目录里有没有 epub
        for root, _, files in os.walk(tempdir):
            for f in files:
                if f.lower().endswith('.epub'):
                    return parse_epub(os.path.join(root, f))
        # 否则把 html 当单章
        if filepath.lower().endswith(('.html', '.htm')):
            from bs4 import BeautifulSoup
            from .common import is_chapter_title
            html = open(filepath, 'r', encoding='utf-8', errors='replace').read()
            soup = BeautifulSoup(html, 'lxml')
            for t in soup(['style', 'script', 'nav']):
                t.decompose()
            text = soup.get_text(separator='\n', strip=True)
            # 用章节标题正则再切
            lines = text.split('\n')
            chapters = []
            cur_title = '正文'
            cur_buf = []
            for line in lines:
                if is_chapter_title(line):
                    if cur_buf:
                        chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})
                    cur_title = line.strip()
                    cur_buf = []
                else:
                    cur_buf.append(line)
            if cur_buf:
                chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})
            return [c for c in chapters if len(c['text']) >= 50] or [{'title': '全文', 'text': text}]
        raise ValueError(f"mobi 解包后无法识别的格式: {filepath}")
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(tempdir, ignore_errors=True)
        except Exception:
            pass
