#!/bin/bash
# 高标科技压力测试报告构建管线：探测解释器 -> 必要时装 reportlab -> 生成报告 -> 校验产物
set -u
GAO=/home/coordinate35/hermes_data/ipos/gaobiao
RLV=/home/coordinate35/hermes_data/rl-venv
PDF="$GAO/高标科技压力测试报告_20260916_v2.pdf"
GEN_PY=""

probe() { "$1" -c "import reportlab" >/dev/null 2>&1; }

echo "== [0] 探测现有解释器 =="
for PY in "$RLV/bin/python" "$(command -v python3 || true)" /usr/bin/python3; do
  [ -n "${PY:-}" ] && [ -x "$PY" ] || continue
  echo "try: $PY"; "$PY" --version 2>&1
  if probe "$PY"; then GEN_PY="$PY"; echo "HAVE_RL: $PY"; break; fi
done

if [ -z "$GEN_PY" ]; then
  echo "== [1] 安装 reportlab =="
  echo "-- net probe --"
  timeout 6 curl -sI https://pypi.org/simple/ 2>&1 | head -1
  echo "probe_done"
  if command -v uv >/dev/null 2>&1; then
    echo "-- uv venv --"
    if [ ! -x "$RLV/bin/python" ]; then uv venv "$RLV" 2>&1 | tail -2; fi
    for IDX in "" "-i https://pypi.tuna.tsinghua.edu.cn/simple" "-i https://mirrors.aliyun.com/pypi/simple"; do
      [ -n "$IDX" ] && echo "-- retry: $IDX --"
      timeout 150 uv pip install --python "$RLV/bin/python" $IDX reportlab 2>&1 | tail -2
      probe "$RLV/bin/python" && break
    done
    if probe "$RLV/bin/python"; then GEN_PY="$RLV/bin/python"; echo "INSTALLED_UV"; fi
  fi
  if [ -z "$GEN_PY" ] && command -v pip3 >/dev/null 2>&1; then
    echo "-- pip3 --user --"
    timeout 150 pip3 install --user reportlab 2>&1 | tail -2
    for PY in "$(command -v python3)" /usr/bin/python3; do probe "$PY" && GEN_PY="$PY" && break; done
    if [ -z "$GEN_PY" ]; then
      timeout 150 pip3 install --user -i https://pypi.tuna.tsinghua.edu.cn/simple reportlab 2>&1 | tail -2
      for PY in "$(command -v python3)" /usr/bin/python3; do probe "$PY" && GEN_PY="$PY" && break; done
    fi
    [ -n "$GEN_PY" ] && echo "INSTALLED_PIP"
  fi
fi

echo "GEN_PY=${GEN_PY:-NONE}"
if [ -z "$GEN_PY" ]; then
  echo "-- 无 reportlab，退回 Markdown 模式 --"
  "$(command -v python3)" "$GAO/build_report.py" --md-only
  echo "DONE_MD_ONLY"; exit 0
fi

echo "== [2] 构建报告 =="
"$GEN_PY" "$GAO/build_report.py" 2>&1 | tail -45
echo "== [3] 产物校验 =="
ls -l "$GAO"/高标科技压力测试报告_20260916_v2.md 2>&1
ls -l "$PDF" 2>&1
file "$PDF" 2>&1
if command -v pdftotext >/dev/null 2>&1; then
  pdftotext "$PDF" /tmp/gaobiao_report_check.txt 2>&1
  echo "-- 文本抽样 --"
  head -c 400 /tmp/gaobiao_report_check.txt; echo
  echo "count_临界点=$(grep -c 临界点 /tmp/gaobiao_report_check.txt)"
  echo "count_高标=$(grep -c 高标 /tmp/gaobiao_report_check.txt)"
fi
command -v pdfinfo >/dev/null 2>&1 && pdfinfo "$PDF" 2>&1 | grep -E "Pages|File size"
if [ -s "$PDF" ]; then echo "PDF_PRESENT"; else echo "PDF_MISSING_AFTER_BUILD"; fi
echo "DONE_OK"
