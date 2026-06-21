---
name: weixin-article-archiver
version: 1.0.0
description: >
  完整归档微信公众号文章，包括纯文本提取、图片下载、AI视觉分析、
  图文合并存档。支持自动识别封面、正文配图、信息图、头像等全部图片资源。
tags: [weixin, 微信, 公众号, 文章归档, 图片下载, 视觉分析]
---

# 微信公众号文章完整归档

## 使用场景

用户提供了微信公众号文章链接，需要：
1. 保存文章文字内容
2. 下载文章中的所有图片
3. 对图片进行AI视觉分析，提取图中信息
4. 将文字和图片附录合并为一个完整归档

## 步骤

### Step 1: 解析文章URL，提取基础信息

使用 `requests` + `BeautifulSoup` 抓取HTML，提取：
- 标题 (`rich_media_title` 或 `og:title` meta)
- 公众号名称 (`js_name` 或 `profile_nickname`)
- 发布时间 (`publish_time`)
- 正文 (`js_content` 或 `rich_media_content`)

```python
import requests
from bs4 import BeautifulSoup

url = "https://mp.weixin.qq.com/s/xxxxx"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MicroMessenger/7.0.20"
}
resp = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')

title = (soup.find('h1', class_='rich_media_title') or soup.find('h2', class_='rich_media_title'))
title = title.get_text(strip=True) if title else soup.find('meta', property='og:title').get('content', '')

nickname = (soup.find('a', id='js_name') or soup.find('span', class_='profile_nickname'))
nickname = nickname.get_text(strip=True) if nickname else ''

publish_time = soup.find('em', id='publish_time')
publish_time = publish_time.get_text(strip=True) if publish_time else ''

content_div = soup.find('div', id='js_content') or soup.find('div', class_='rich_media_content')
```

**注意：**
- 微信公众号HTML使用了重度的行内样式和 `section` 嵌套，提取正文时建议先遍历 `section` 标签，没有时再整体获取文本。
- 部分文章的发布时间在HTML中可能为空，属于正常情况。

### Step 2: 下载所有图片

公众号文章中的图片使用懒加载，`src` 属性可能是占位符，真实URL在 `data-src` 中。

```python
import os
from urllib.parse import urlparse

imgs = soup.find_all('img')
img_dir = os.path.join(base_dir, f"{safe_title}_images")
os.makedirs(img_dir, exist_ok=True)

for i, img in enumerate(imgs):
    src = img.get('data-src') or img.get('src', '')
    if not src or 'mmbiz' not in src:
        continue
    # 下载图片
    img_resp = requests.get(src, headers=headers, timeout=30)
    ext = os.path.splitext(urlparse(src).path)[1] or '.jpg'
    filename = f"img{i+1}{ext}"
    with open(os.path.join(img_dir, filename), 'wb') as f:
        f.write(img_resp.content)
```

**图片分类识别：**
- 第一张图：通常是封面图 (`cover`)
- `alt`含"作者头像"：作者头像 (`avatar`)
- 中间图片：正文配图 (`img4`, `img5` 等)

### Step 3: AI视觉分析图片

对每张下载的图片使用 `vision_analyze` 工具进行分析。这对信息图特别重要，因为其中可能包含大量文字、表格、框架等结构化内容，纯文本提取无法获取。

**使用提示词：**
```
"这是什么图片？描述其内容"
```

**VISION_ANALYZE 对信息图的优势：**
- 能够识别图中的文字、表格、阶段划分
- 能够提取逻辑框架和战略路径
- 例如："五个推进阶段"、"三层结构"等

### Step 4: 合并存档

将所有内容写入一个 `.txt` 文件，末尾追加【图片附录】。

```
标题: xxx
公众号: xxx
发布时间: xxx
原文链接: xxx
保存时间: xxx
============================================================

[正文内容...]

============================================================
【图片附录】
原文共包含 X 张图片，已下载至: /path/to/images/

[【cover.jpg】 (xx KB)
  内容: AI视觉分析结果...]

[【img4.jpg】 (xx KB)
  内容: AI视觉分析结果...]
```

## 文件存储结构

```
/home/coordinate35/hermes_data/
├── 文章标题.txt                          # 主文件
└── 文章标题_images/                     # 图片目录
    ├── cover.jpg                          # 封面图
    ├── img4.jpg                           # 正文配图1
    ├── img5.jpg                           # 正文配图2
    ├── img6.jpg                           # 正文配图3
    └── avatar.jpg                         # 作者头像
```

## 常见问题与解决方案

| 问题 | 解决方案 |
|------|----------|
| 验证页面拦截 | 使用微信浏览器User-Agent，如 MicroMessenger/7.0.20 |
| 发布时间为空 | 部分文章没有发布时间字段，属于正常，留空即可 |
| 图片下载失败 | 检查 `data-src` vs `src`，公众号使用懒加载 |
| 信息图无法OCR | 必须使用AI视觉分析，普通OCR无法提取逻辑结构 |
| 标题含特殊字符 | 使用 `c if c.isalnum() or c in (' ', '-', '_') else '_'` 转换 |

## 工具链接

- `requests`、`BeautifulSoup` 用于爬取
- `vision_analyze` 用于图片内容识别
- 文件保存到 `/home/coordinate35/hermes_data/`

## 微信长消息处理

向用户发送长文时需注意微信消息长度限制（单条不超过1500字符）。详见 `references/weixin-long-message-handling.md` — 分段策略、序号标注、收尾确认等完整流程。
