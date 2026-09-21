---
name: doubao-thread-archive
version: 1.0.0
description: Use when 保存/归档豆包分享链接内容及文件（含飞书幻灯片）。
author: hermes
license: MIT
metadata:
  tags: [归档, 豆包, doubao, 飞书幻灯片, 截图]
---

# 豆包分享链接归档（doubao.com/thread/<share_id>）

用户发来豆包分享链接要求"保存/存档/下载内容，包括里面的文件"时使用。2026-09-21 实测通过。

## When to Use（命中即用）

- 用户发来 `www.doubao.com/thread/<id>` 或 `doubao.com/chat/...` 链接，要求"保存/存档/下载/存下来"，含或不含"包括里面的文件"
- 提到豆包做的东西（PPT/文档/表格）要取回本地

## 关键事实（先读）

1. `web_extract` 抓不到（JS SPA），直接 curl + 解码 HTML。
2. **完整数据嵌在分享页 HTML 的 `<script data-fn-name="mergeLoaderData" data-fn-args="...">` 属性里**，多层转义。解码链：`html.unescape` → `json.loads`（顶层 list）→ 递归找 `routerDataFnArgs` 里的字符串项再 `json.loads` → `{data: {share_info, message_snapshot}}`。用 `scripts/decode_share.py`。
3. `message_snapshot.message_list` 通常**只有最后一轮**（用户 1 条 + 豆包回复 1 条），不是完整会话历史——交付时必须如实说明。完整历史需登录豆包。
4. 消息块类型：`10000` text_block / `10040` thinking_block（步骤标题）/ `10019` file_operation_block（沙盒命令与输出）/ `10025` search_query_result_block（联网搜索引用）/ `10030` artifact_block（产出文件）。
5. **产出文件主要是飞书幻灯片**（resource_type 9）。打开链接在 fileop 的 `lark-cli slides +create` 输出中：`https://my.feishu.cn/slides/<id>`，**无需登录即可查看**（游客模式）。
6. 需登录才能拿的（放弃并说明）：豆包内网预览 `internal-api-space.feishu.cn/...`、豆包沙盒文件、可编辑 PPTX 导出。
7. 部分 fileop 的 content 为空 = 源数据本身如此（"完整内容暂不支持展示"），如实保留，不要杜撰。

## 流程

1. **抓页面**：`curl -sL -A "<Chrome UA>" "https://www.doubao.com/thread/<id>" -o share_page.html`（注意：单条命令，不做管道复合，防 QQ 场景安全审批挂起）
2. **解码**：`python3 scripts/decode_share.py share_page.html share_payload.json` → 得 raw 数据
3. **转录**：用 `scripts/assemble_archive.py` 生成逐字 markdown（思考步骤/搜索/文件操作/产出文件全部保留，禁止概括）+ 复制 raw + 幻灯片 PNG→PDF
4. **幻灯片截图**（浏览器）：打开飞书链接 →
   - 先隐藏覆盖层：`.ssrWaterMark`、`.ai-water-marker-text`、`.lKrd`（缩放控件）、`.help-block`（右下帮助按钮）→ `el.style.display='none'`
   - `.slide-item-wrapper` 列表 = 页数；点第 i 个切页；`.slide-canvas`.innerText = 该页文字版
   - `cdp('Emulation.setDeviceMetricsOverride', width=1440, height=860, deviceScaleFactor=1)` 放大视口 → 取 `.slide-canvas-boundary` box → `cdp('Page.captureScreenshot', format='png', clip={x,y,width,height,scale:2})`
   - **captureScreenshot IPC 5s 超时很常见 → 必须写重试循环（3-4 次）**
   - vision_analyze 验证：内容完整、无水印/控件、无裁切
5. **PDF**：`python3 scripts/md2pdf_transcript.py in.md out.pdf "<页脚>"`（需 rl-venv：`~/hermes_data/rl-venv/bin/python`）
6. **归档目录**：`~/hermes_data/doubao_threads/<日期>_<分享名>/`，结构：`会话记录*.md/.pdf` + `files/`（PNG+PDF+文字版）+ `raw/`（share_payload.json + share_page.html）
7. **交付**：QQ 主回复 = 文字 + 非音频 MEDIA（默认发 PDF，.md 手机端打不开）；说明归档目录路径、分享仅含最后一轮、可编辑版在飞书链接。
   **语音摘要单独投递**（音频必须独占整条消息，与文字/文件混排会被 QQ 丢弃音频；实测 4 次）：
   - 语音稿写 /tmp/xxx_text.txt → `bash ~/.hermes/scripts/win_tts.sh "$(cat 稿.txt)" /tmp/xxx.wav`（三级降级链见 voice-message-delivery skill）
   - 写 `echo "MEDIA:/tmp/xxx.wav"` 的一次性脚本到 ~/.hermes/scripts/
   - `cronjob create`：schedule=ISO(now+150s)、deliver=origin、no_agent=true、script=该脚本
   - 主回复先发（文字+文件），语音约 2 分钟后单独到达

## Pitfalls

- `data-fn-args` 属性值内可能含 `>` 字符：**不能用 `find('>')` 找标签结束**，要用 `find('"')` 定位属性值结尾。
- md2pdf 的 `<br/>`：必须先逐行 `html.escape` 再拼 `<br/>`，否则标签被转义成字面文本（曾踩坑）。
- 字体：wqy-zenhei 全覆盖除 `､`(U+FF64)，PDF 渲染层替换为 `、`（md 保留原文）。脚本已内置。
- 幻灯片的"两页"以 `.slide-item-wrapper` 实际数量为准（曾误以为 1 页，实为 2 页）——分享对话只覆盖了其中一页的制作过程。
- CDP clip 的 scale=2 输出 ~2488×1472；重试循环内 sleep 2s。

## 脚本

- `scripts/decode_share.py` — HTML→share_payload.json
- `scripts/assemble_archive.py` — payload→逐字转录 md + 归档目录组装
- `scripts/md2pdf_transcript.py` — 受控 markdown 子集→PDF（reportlab，中文 OK）
