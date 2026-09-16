---
name: article-archive
version: 1.0.0
description: Use when 用户要归档/存档文章（卢麒元微博/长微博/头条/截图）。截图逐字转录+元信息存 markdown。
author: hermes
license: MIT
metadata:
  tags: [归档, 文章, 卢麒元, 转录, 截图]
---

# 作者文章归档（卢麒元微博/头条/长微博/截图）

用户长期收集卢麒元文章，归档目录：`~/hermes_data/weibo_data/articles/<标题>_<日期>.md`。

## When to Use（命中即用，不看措辞）

- "归档" / "存档" / "存起来" + 文章 / 微博 / 长微博 / 头条 / 图片 / 截图
- 用户发来文章截图/长图（vision 可见全文）要求保存
- 卢麒元文章（微博、头条文章、长微博、公众号转帖）

## 流程

1. **先看已有文件格式**：`search_files pattern="*.md" path=~/hermes_data/weibo_data/articles`，以最新归档为模板（元信息块结构、分隔线、注释习惯），保持全库一致。
2. **获取全文**：
   - 图片截图 → `vision_analyze`，提示词明确要求"完整、逐字读出全部文字内容，不要概括"；一次没读全就追问"继续"或分块。
   - 网页/链接 → 抓取正文；网络抓取失败的会话里可直接用图片转录。
     - 官方站点文章（求是网/政府站等，2026-09 首用）：`curl -sSL -o /tmp/page.html "<URL>"` 抓 HTML → Python stdlib 正则剥 script/style 后按标签转行 → 按正文起止标记切片，全文照录（不概括）→ md 加元信息头（作者/来源/发布日期/原文链接）。此法不依赖 web_extract/browser（二者都可能临时故障）。
     - 非卢麒元的通用文章存 `~/hermes_data/articles/<作者>_<标题>_<来源>_<日期>.md`；页面图注保留并标 `［图注］` 前缀。
     - **交付到 QQ 默认转 PDF**（手机端打不开 .md）：`~/hermes_data/rl-venv/bin/python ~/hermes_data/articles/build_article_pdf.py "<文章.md>"` → 同目录同名 .pdf（reportlab + wqy 字体，含章节标题 KeepTogether 防孤行，均已实测）；校验链：pdfinfo 页数 + pdftotext 关键句 + pdftoppm→vision 抽页。
     - **正文配图一并补齐**（2026-09-16 实测）：从源页 HTML 提取 `<img>` 真实地址（排除导航/二维码图标）→ curl 存 `images/` → md 在 `［图注］` 行前加 `![图](images/...)` → PDF 脚本自动嵌图（12cm 宽居中 + 图注紧随，KeepTogether）。图注在 md 里保留 `［图注］` 前缀；压缩版面时图片收宽是防"尾页孤行"的主杠杆。
3. **写 markdown**（模板，对齐已有文件的元信息格式）：

   ```markdown
   # 标题

   > **作者**：卢麒元
   > **发布**：YYYY-MM-DD HH:MM · 来源平台（微博长微博/头条文章）
   > **来源**：URL 或 "用户提供截图转录，原文链接未记录"
   > **UID**：1245732825（卢麒元微博 UID，可查已有文件）
   > **转录时间**：YYYY-MM-DD（CST）

   ---

   正文全文（忠实原文，保留空行分段）

   —— 卢麒元

   ---

   *注：文内引用处补出处（如"红雨随心翻作浪"出自《七律二首·送瘟神》1958；"俏也不争春"出自《卜算子·咏梅》1961）；原词为"她在丛中笑"时按截图转录为"他"则如实标注。*
   ```

4. **命名**：`<标题>_<YYYY-MM-DD>.md`（日期取原文发布时间，非归档时间）。

## Pitfalls

- 不要概括正文——用户要求逐字原文（记忆：文档阅读须逐字念原文，不可概括）。
- 转录的文字如与知名诗词原文有出入（如"他"vs"她"），保留截图原样，在注释中说明，不要擅自改。
- 归档后简要报告路径和条数；可提示与同目录已有文章的关系（如《论体面》同作者）。
- 与 `weixin-article-archiver` 的分工：公众号文章链接爬取用那个 skill；微博/头条/长微博/图片截图归档用本 skill。
