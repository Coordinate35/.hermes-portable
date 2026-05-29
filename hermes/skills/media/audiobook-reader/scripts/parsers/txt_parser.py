"""TXT 解析器：编码探测 + 章节切分。"""
import chardet
from .common import is_chapter_title


def parse_txt(path: str):
    """返回 [{title, text}, ...]"""
    # 编码探测：读 200KB 提高准确率
    with open(path, 'rb') as f:
        raw = f.read(200_000)
    detected = chardet.detect(raw)
    enc = (detected.get('encoding') or 'utf-8').lower()
    # 中文常见编码归一
    if enc in ('gb2312', 'gbk'):
        enc = 'gb18030'

    try:
        with open(path, 'r', encoding=enc, errors='replace') as f:
            content = f.read()
    except (LookupError, UnicodeDecodeError):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

    lines = content.split('\n')

    chapters = []
    cur_title = '正文'
    cur_buf = []
    for line in lines:
        if is_chapter_title(line):
            if cur_buf and any(l.strip() for l in cur_buf):
                chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})
            cur_title = line.strip()
            cur_buf = []
        else:
            cur_buf.append(line)
    if cur_buf and any(l.strip() for l in cur_buf):
        chapters.append({'title': cur_title, 'text': '\n'.join(cur_buf).strip()})

    # 过滤太短的章节（可能是误匹配的扉页）
    chapters = [c for c in chapters if len(c['text']) >= 50]

    # 如果没切出来或只有 1 章，整本作为单章
    if not chapters:
        chapters = [{'title': '全文', 'text': content.strip()}]

    return chapters
