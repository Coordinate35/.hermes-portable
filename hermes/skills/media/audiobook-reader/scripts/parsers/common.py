"""通用工具：段落切分、章节切分正则、文本清洗。"""
import re

CHAPTER_PATTERNS = [
    # 中文回/章/节/卷/篇
    re.compile(r'^\s*第\s*[一二三四五六七八九十百千零〇两\d]+\s*[回章节卷篇]\s*.{0,80}$'),
    # 英文 Chapter
    re.compile(r'^\s*Chapter\s+\d+', re.IGNORECASE),
    # 中文 "卷一" 之类
    re.compile(r'^\s*卷\s*[一二三四五六七八九十百\d]+\s*.{0,80}$'),
    # 前言/序言/后记/楔子等单独标题（独占一行且短）
    re.compile(r'^\s*(前言|序言|楔子|引子|后记|尾声|跋|序章|终章)\s*.{0,30}$'),
    # 附录一/附录二/附录 1 之类
    re.compile(r'^\s*附录\s*[一二三四五六七八九十百\d]*\s*.{0,80}$'),
]


def is_chapter_title(line: str) -> bool:
    """判断一行是否是章节标题。"""
    line = line.strip()
    if not line or len(line) > 100:
        return False
    for p in CHAPTER_PATTERNS:
        if p.match(line):
            return True
    return False


def split_into_paragraphs(text: str, min_len: int = 50, max_len: int = 500):
    """将一段长文本切成段落数组。
    1. 按 \n 初切
    2. 合并相邻短段（合并后 <= max_len 才合并）
    3. 切分超长段（按句号、感叹号、问号切）
    """
    raw = [p.strip() for p in re.split(r'\n+', text) if p.strip()]
    # 合并短段
    merged = []
    buf = ''
    for p in raw:
        if not buf:
            buf = p
            continue
        if len(buf) < min_len and len(buf) + len(p) + 1 <= max_len:
            buf = buf + ' ' + p
        else:
            merged.append(buf)
            buf = p
    if buf:
        merged.append(buf)

    # 切分超长段
    result = []
    for p in merged:
        if len(p) <= max_len:
            result.append(p)
            continue
        # 按句号切
        sentences = re.split(r'(?<=[。！？!?])', p)
        cur = ''
        for s in sentences:
            if not s.strip():
                continue
            if len(cur) + len(s) <= max_len:
                cur += s
            else:
                if cur:
                    result.append(cur)
                cur = s
        if cur:
            result.append(cur)

    return [p for p in result if p.strip()]
