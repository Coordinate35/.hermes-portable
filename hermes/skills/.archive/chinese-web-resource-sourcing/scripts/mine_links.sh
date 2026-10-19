#!/bin/bash
# mine_links.sh — so.com（360搜索）快照挖链：找网盘分享链接/提取码 + 结果真实 URL
# Usage: bash mine_links.sh "<关键词>"
#   例：bash mine_links.sh '如何快速了解一个行业 提取码'
# 说明：单站 curl（低风险）；输出三段：网盘链接/提取码、data-mdurl 真实 URL、结果标题。
set -u
KW="$1"
if [ -z "$KW" ]; then
  echo "usage: $0 '<keyword>'" >&2
  exit 1
fi
OUT=/tmp/so_mine.html
curl -sG --max-time 15 "https://www.so.com/s" \
  --data-urlencode "q=$KW" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  -o "$OUT"
echo "== 网盘链接 / 提取码 =="
grep -oE '(pan\.(baidu|quark)\.(com|cn)[A-Za-z0-9/_.?=-]{4,}|alipan\.com/s/[A-Za-z0-9]+|aliyundrive\.com/s/[A-Za-z0-9]+|lanzou[a-z]?\.[a-z]+/[A-Za-z0-9]+|123pan\.com/s/[A-Za-z0-9_-]+|提取码[:：]?[ ]?[a-z0-9]{4}|访问码[:：]?[ ]?[a-z0-9]{4})' "$OUT" | sort -u || true
echo "== 结果真实 URL（data-mdurl）=="
grep -oE 'data-mdurl="[^"]+"' "$OUT" | sed 's/data-mdurl="//; s/"$//' | sort -u | head -40 || true
echo "== 结果标题 =="
grep -oP '<h3[^>]*>.*?</h3>' "$OUT" | sed 's/<[^>]*>//g' | head -12 || true
