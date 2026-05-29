# 爬在线阅读站的实战经验

当目标书只能从在线阅读站（HTML 章节页）取得，没有 epub/mobi/txt 下载链接时的处理流程。基于 2026-05 抓 jinyong.net.cn 三联修订版射雕英雄传的实战总结。

## 1. 反爬检测：见到这些立即换站

不要硬刚反爬，浪费时间。换源永远比绕验证快。

| 症状 | 含义 |
|------|------|
| HTTP 302 → `/GE/CC/VALIDATOR?key=...&url=...` | 自建 token 验证（jinyongx.com 用的就是这套），需 JS 执行 |
| HTTP 403 + 页面提示"Just a moment..." | CloudFlare 五秒盾 |
| HTTP 200 但 body 是 JS challenge / `<script>document.cookie=...</script>` 才能拿真页面 | JS-rendered challenge |
| 首次请求返回 200 但内容是登录墙/付费墙 | 需会话 cookie |
| 同一书有多个站点，其中一个反爬 | 直接换没反爬的那个，**不要试 cookie/UA/proxy 绕** |

**反爬识别命令**：
```bash
curl -sI --max-time 10 -A "Mozilla/5.0" -H "Referer: <主页>" "<目标URL>" | head -5
# 看 HTTP 状态 + Location 头
```

## 2. 同一本书多站点对比

爬之前先用 Bing 搜「<书名> <版本关键词> 在线阅读」拿到 3+ 个候选站，列出来：

| 站点 | URL 模式 | 章节数 | 反爬 | 推荐 |
|------|---------|--------|------|------|
| jinyong.net.cn | http://jinyong.net.cn/<bookname>/NNN.html | 43 | ❌ 无 | ✅ 首选 |
| jinyongx.com | https://jinyongx.com/<bookname>/NNN.html | 43 | ✅ token 302 | ❌ 跳过 |
| wyshu.com | https://www.wyshu.com/wx/NNN/ | - | 内容差 | ❌ 备选 |

**先 curl 一页 + grep `<title>` + 检查首段内容长度**，确认拿得到再开爬。

## 3. 版本辨识（金庸为例）

修订版（三联版）vs 新修版可以从开篇第一句辨识：

| 版本 | 射雕第一句关键差异 |
|------|------|
| **三联修订版**（1980 年代） | "...从**临安**牛家村边绕过..." |
| **新修版**（2003 年后） | "...从**两浙西路临安府**牛家村边绕过..." |
| 章节数 | 修订版 40 回，新修版 41 回 |
| 章节命名 | 原书都是"第X回"，但在线站经常自作主张改成"第X章"，需还原 |

**好习惯**：导入前 grep 第一回开头确认版本，避免后续投诉。

## 4. 章节链接抓取与编号映射

很多站章节 id 是反序的（id 越大 = 章节越靠前 或 反之）。先把目录页爬下来，做 (id → 章节序号) 映射：

```python
soup = BeautifulSoup(open('index.html', encoding='utf-8'), 'lxml')
links = []
for a in soup.find_all('a', href=re.compile(r'^/<bookname>/\d+\.html$')):
    text = a.get_text(strip=True)
    if text:
        links.append((a['href'], text))
# 打印出来人眼核对一下 id 和章节标题的对应关系，再写映射表
```

## 5. HTML 正文提取 — 噪音清理标准模板

在线阅读站的正文 div 周围塞满了导航/字号控件/版权/SEO 文案。模板做法：

### Step 1: 定位正文 div
按以下顺序尝试：
1. `soup.find('div', id='content')`
2. `soup.find('div', class_='body-content')` / `'showtxt'` / `'chapter-content'` / `'vcon'`
3. 兜底：找文本最长的 div

### Step 2: 删除噪音子标签
```python
for tag in content_div.find_all(['script', 'style', 'a', 'select', 'button', 'input']):
    tag.decompose()
```
**注意**：不要无脑删 `<div>`，因为段落经常也用 div 包。

### Step 3: 关键词黑名单逐行过滤
基于 jinyong.net.cn 实测的清单（按需追加）：
```python
skip_keywords = [
    # 站点控件
    '官网：', '选择背景色', '选择字体', '恢复默认', '←上一章', '下一章：',
    '黄橙', '洋红', '淡粉', '水蓝', '草绿', '白色',
    '宋体', '黑体', '微软雅黑', '楷体',
    # 品牌/SEO
    'JinYong.NET', '欢迎收藏', '请记住本站',
    '一秒钟记住', '记住本站网址', '过目不忘', '拼音全拼写',
    # 版权
    '网友推荐顺序', '版权永归', '本站只做演示', 'Copyright', 'by 金庸',
    '请支持正版', 'admin@', '铁杆粉丝',
    # 章节头部装饰
    '小说：', '作者：', '小说类型',
]
```

### Step 4: 截断点（END_MARKERS）—— 这是关键技巧

页面底部常有大段"扩展阅读""相关推荐""版本说明"等噪音区，黑名单逐行删不干净（很多是相对长的句子）。更可靠的做法是**找到第一个出现的截断标记，从那行直接切掉后续所有内容**：

```python
END_MARKERS = [
    '扩展阅读', '金庸小说的三大版本', '金庸小说有三个版本',
    '版本影视作品', '影视资源', '快捷键',
    '小说阅读顺序', '金庸推荐顺序', '小说历史顺序', '小说创作顺序',
    '版权声明', '上一章：', '下一章：',
]
cut = len(lines)
for i, line in enumerate(lines):
    if any(m in line for m in END_MARKERS):
        cut = i
        break
lines = lines[:cut]
```

实测：jinyong.net.cn 第一回原本提取出 28444 字（含噪音），加 END_MARKERS 截断后 27400 字（纯正文）。

### Step 5: 短噪音过滤
切完后可能还有零星单字漂浮（如孤立的"金庸"两字），但只要不影响段落切分就放过。`add_book.py` 段落合并阈值会自动把这种短段合到上一段去。

### Step 5.5: 站方署名残留 — 必须在 crawler 阶段干掉

实测 jinyong.net.cn 每章末尾都有孤立的"**金庸**"两字（站方版权署名），位置在所有 END_MARKERS 之后但又在 `</div id=content>` 之内。这种残留：

- 不影响段落切分（合并到上一段）
- **但 TTS 念到末段会多读 2 字"金庸"** — 影响听感
- 完整性核查 (`verify_book.py`) 会扫到末段不以正常标点收尾 → 触发警告

**正确的修复点是 crawler 而不是 import**：在 `skip_keywords` 里加入站方专属署名（"金庸"、"by 作者名" 等），重爬即可。导入后再回补很麻烦（要逐章 sed 后重导入，还要保留 progress.json）。

**预防 checklist**：每写一个新站点的 crawler，最后 grep 一遍 `tail -c 50` 看末尾是不是干净，**不干净就回去补 skip_keywords，不要 import 后再说**。

## 6. 章节标题规范化

站方标题往往不是原书格式，需还原：

```python
CN_NUMS = ['零', '一', '二', '三', ..., '四十']

def normalize_main_title(order, raw_title):
    # "第01章 风雪惊变" → "第一回　风雪惊变"
    m = re.match(r'^第\s*\d+\s*章[\s　]*(.+)$', raw_title)
    name = m.group(1).strip() if m else raw_title.strip()
    cn = CN_NUMS[order] if order < len(CN_NUMS) else str(order)
    return f'第{cn}回　{name}'  # 注意是全角空格 \u3000
```

全角空格 `　` 在中文章节标题里很重要，原书都用这个分隔。

## 7. 抓取节奏与中断恢复

- **延迟**：每页 1.0-1.5 秒，礼貌为主，避免被风控
- **重试**：网络异常重试 3 次，每次间隔 3s
- **40+ 章的爬取耗时**：约 1-2 分钟，**必须用 `background=true + notify_on_complete=true`**，foreground 会被 300s 超时杀掉中途丢数据
- **断点续传**：理想做法是每爬完一章就追加写文件，这样中断也能续。当前 `crawl_jinyongnet_shediao.py` 是一次性写出，下次改进可加增量写

## 8. 总流程清单

1. Bing 搜书 + 候选站列表
2. curl + Referer 头测可达性 + 反爬检测（看 302/403/JS challenge）
3. 拿目录页，建 id→章节序号映射
4. 单章 curl 验证正文提取质量（重点看首/末 300 字有没有噪音）
5. 微调 skip_keywords + END_MARKERS 直到干净
6. 验证版本（grep 第一句关键差异）
7. **`background=true + notify_on_complete=true`** 开爬
8. 写成 txt → `add_book.py --source <txt> --title "<书名>（<版本>）" --version "<版本>" --author "<作者>"`

## 已验证的 crawler 脚本

`scripts/crawl_jinyongnet_shediao.py` 是按本规范实现的参考代码。
其他金庸作品同源（jinyong.net.cn）可复制此脚本改 BASE_URL + 章节 id 范围即可。
