"""parsers 包入口：根据扩展名分发。"""
import os
from .common import split_into_paragraphs


def parse_book(path: str):
    """根据文件扩展名分发解析器，返回 [{title, text}, ...]。"""
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    if ext == 'epub':
        from .epub_parser import parse_epub
        return parse_epub(path)
    if ext == 'txt':
        from .txt_parser import parse_txt
        return parse_txt(path)
    if ext == 'mobi':
        from .mobi_parser import parse_mobi
        return parse_mobi(path)
    if ext == 'pdf':
        raise NotImplementedError("pdf 格式暂未实现，遇到再补 parsers/pdf_parser.py")
    raise ValueError(f"不支持的格式: .{ext}")


__all__ = ['parse_book', 'split_into_paragraphs']
