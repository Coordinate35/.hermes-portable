#!/usr/bin/env python3
"""Byte-diff the 📄 完整原文 block of a draft delivery against the authoritative text
(show raw_text, falling back to text_stripped.rstrip()) from a wb_verify_<id>.json.

Usage:
    python3 wb_diff_check.py <draft_file> <wb_verify_json>

Exit 0 = byte-identical; 1 = mismatch (prints first diff context); 2 = extract failed.
"""
import sys
import re
import json


def main() -> int:
    draft_path, verify_path = sys.argv[1], sys.argv[2]
    with open(draft_path, encoding="utf-8") as f:
        draft = f.read()
    with open(verify_path, encoding="utf-8") as f:
        vj = json.load(f)

    baseline = vj.get("raw_text")
    if not baseline:
        baseline = (vj.get("text_stripped") or "").rstrip()

    # Block ends at the notes marker, or at an attached 【转发 ...】 block
    # (repost-with-comment posts put the retweeted text between 原文 and 注).
    m = re.search(r"📄 完整原文\n(.+?)\n\n(?:📎 注|【转发 )", draft, re.S)
    if not m:
        print("EXTRACT FAIL: block end marker (\\n\\n📎 注 or \\n\\n【转发) not found in draft")
        return 2
    block = m.group(1)

    print(f"baseline_len={len(baseline)} block_len={len(block)}")
    print(f"baseline_repr_tail={baseline[-25:]!r}")
    print(f"block_repr_tail={block[-25:]!r}")

    if block == baseline:
        print("DIFF: 0 (byte-identical)")
        return 0

    n = min(len(block), len(baseline))
    for i in range(n):
        if block[i] != baseline[i]:
            print(f"first mismatch at index {i}:")
            print(f"  block   : {block[max(0, i - 40):i + 40]!r}")
            print(f"  baseline: {baseline[max(0, i - 40):i + 40]!r}")
            return 1
    print("one string is a prefix of the other; tail diff:")
    print(f"  block tail   : {block[n - 30:]!r}")
    print(f"  baseline tail: {baseline[n - 30:]!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
