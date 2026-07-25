---
name: weibo-monitoring
title: 微博账号监控与防重复推送
description: 监控指定微博账号的新内容，实现防重复推送机制，避免API窗口变化导致的误判
---

# 微博账号监控

## 概述

监控指定微博账号的新内容，通过ID级去重机制防止重复推送。

## 核心问题与解决方案

### 问题：API窗口变化导致重复推送
- 微博API只返回最近10条微博
- 当账号活跃时，旧微博被挤出列表
- 脚本误判旧微博为"新"内容，导致时间戳倒退
- 下次运行时又把这些"旧"微博当成新的推送

### 解决方案：双重防重复机制
1. **时间戳比较**：`created_at > last_time`
2. **ID去重**：`weibo_id not in pushed_ids`

## 文件结构

```
~/.hermes/scripts/weibo_monitor.py          # 📄 主文件（定时任务调用）
~/.hermes/hermes-agent/weibo_monitor.py     # 🔗 软链接 → 主文件
~/.hermes/skills/social-media/weibo-account-monitor/scripts/weibo_monitor.py  # 🔗 软链接 → 主文件
```

## 状态文件

位置：`/home/coordinate35/hermes_data/weibo_data/last_weibo.json`

```json
{
  "accounts": {
    "account_name": {
      "last_time": "Fri Apr 25 16:29:49 +0800 2026",
      "pushed_ids": ["id1", "id2", ...],
      "last_check": "2025-04-25T16:30:37"
    }
  }
}
```

## 关键配置

### 定时任务
```yaml
schedule: "*/5 * * * *"  # 每5分钟执行一次
script: weibo_monitor.py
```

### 监控账号（示例）
- 卢麒元 (UID: 1245732825)
- 正心以中and修身以和 (UID: 7951175445)

## 防重复逻辑要点

```python
# 每次运行都把看到的微博ID加入 pushed_ids
for weibo in api_response:
    weibo_id = str(weibo['id'])
    if weibo_id not in pushed_ids:
        pushed_ids.append(weibo_id)
        
# 只推送新的（时间戳和ID都新）
if created_at > last_time and weibo_id not in pushed_ids:
    push_notification(weibo)
```

## 输出规范（用户强制要求）

### 1. 必须直接转发原文
- **严禁LLM做摘要、解读、润色或结构化成报告**
- 脚本输出什么，就原样发给用户，**一字不改**
- 禁止添加标题、分点、emoji装饰、背景解读
- 检测到多条新微博时，**逐条输出**，禁止合并成一篇摘要

### 2. 完整原文，禁止截断
- 旧版 `format_weibo` 曾用 `text[:300]` 截断长微博，**已修复**
- 必须输出微博的完整 `text` 字段，不做长度限制

### 3. 转发/长文微博必须补抓全文

当脚本输出的微博 `text` 在去 HTML 后只剩表情或 <10 字符（如 `[祈祷]`），
**几乎肯定是转发或长文**，必须调以下脚本补抓原文，再附上完整原作者内容：

```bash
cd ~/.hermes/scripts && PYTHONPATH=. python3 \
  ~/.hermes/skills/data-collection/weibo-monitoring/scripts/fetch_mblog_full.py \
  <uid> <weibo_id>
```

返回 JSON 含 `retweet.{user,text,long_text,pic_urls}` 和顶层 `long_text`。
详细字段说明、API 端点、不要踩的坑见
`references/retweet-and-longtext-extraction.md`。

**如果 `long_text` 返回 `[long fetch failed: ...]`**，说明 `/statuses/extend` API 已被反爬拦截（返回 HTML 而非 JSON）。此时必须降级使用浏览器工具访问 `https://m.weibo.cn/detail/{weibo_id}` 并 `browser_snapshot(full=true)` 提取完整内容。详见 `references/retweet-and-longtext-extraction.md` 的"浏览器降级方案"章节。

**禁止**只把表情符号原样发给用户 — 信息量为零。

### 4. 无新微博严格静默
- 没有新微博时，脚本输出 `[SILENT]`
- LLM/Cron job 收到 `[SILENT]` 后**不得发送任何消息**给用户
- 禁止输出"脚本运行正常""本次无新内容"等废话

## 语音播报集成（Auto-TTS）

监控脚本可自动生成语音播报，推送到 QQ/微信时附带语音文件。

### 实现模式

在 `weibo_monitor.py` 检测到新微博后、输出前，调用本地 TTS 服务生成音频：

```python
import subprocess
import json

# 收集待播报文本
voice_texts = []
for w in new_weibos:
    voice_texts.append(f"{w['user']}发布新微博：{w['text']}")

# 生成语音文件
try:
    voice_text = '。'.join(voice_texts)
    voice_path = f"/tmp/weibo_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    payload = json.dumps({"text": voice_text, "text_language": "zh"}, ensure_ascii=False)
    subprocess.run(
        ['curl', '-s', '-X', 'POST', 'http://<tts-host>:<port>',
         '-H', 'Content-Type: application/json',
         '-d', payload, '-o', voice_path, '--connect-timeout', '10'],
        capture_output=True, text=True, timeout=20
    )
    if os.path.exists(voice_path) and os.path.getsize(voice_path) > 1000:
        result += f"\nMEDIA:{voice_path}"
except Exception:
    pass  # 语音失败则静默降级为纯文字
```

### MEDIA: 标记处理

Cron job 的 prompt **必须**指示 agent 原样保留 `MEDIA:/path/to/file` 标记：

```
如果输出中包含 "MEDIA:/path/to/file.wav" 标记，
必须原样保留在你的回复中，不能删除或修改。
MEDIA: 标记是语音文件路径，用于平台原生发送语音消息。
```

如果 agent 删除或改写了 `MEDIA:` 行，语音将不会被发送。

### 推送目标切换

```bash
# 切换到 QQ 推送
hermes cronjob update <job_id> --deliver qqbot

# 切换到微信推送
hermes cronjob update <job_id> --deliver weixin
```

注意：QQ 和微信对语音文件的支持格式不同，TTS 输出格式需与目标平台兼容。

### 参考实现

详细代码补丁和 cronjob prompt 模板见：
`references/auto-tts-integration.md`

## 维护注意事项

1. **状态文件损坏时**：手动填入已知的微博ID到 `pushed_ids`
2. **Cookie过期**：更新 `weibo_monitor.py` 中的 `WEIBO_COOKIE`
3. **脚本路径变更**：更新定时任务配置中的 `script` 字段
4. **TTS 服务变更**：更新脚本中的 TTS endpoint 和超时参数

## 从Cron输出中检索原始微博内容

当浏览器直接访问微博被阻断（Sina Visitor System访客系统）时，可以通过定时任务的本地输出文件获取原始微博全文。

### 文件位置

```
~/.hermes/cron/output/{job_id}/YYYY-MM-DD_HH-MM-SS.md
```

例如：`~/.hermes/cron/output/a27ae1b5f602/2026-04-29_12-54-06.md`

### 文件结构

每个 `.md` 文件包含：
1. **Cron元数据**：job ID、运行时间、调度规则
2. **Script Output**：脚本的原始抓取结果，包含微博的完整原文、发布时间、来源设备、互动数据等
3. **AI分析**：系统生成的摘要报告

### 检索步骤

```bash
# 1. 列出所有定时任务输出目录
ls ~/.hermes/cron/output/

# 2. 找到对应job的最新输出文件
ls -lt ~/.hermes/cron/output/{job_id}/ | head -5

# 3. 直接读取获取原始内容
cat ~/.hermes/cron/output/{job_id}/2026-04-29_12-54-06.md
```

### 关键字段说明

在 `Script Output` 代码块中：
- `📝 内容:` — 微博的完整原文（含回复链接）
- `🕐 时间:` — 原始发布时间（RFC2822格式）
- `📱 来源:` — 发布设备
- `🆔 ID:` — 微博ID（用于构建分享链接）
- `📊 互动:` — 转发/评论/点赞数

### 适用场景

| 场景 | 方法 |
|:---|:---|
| 微博被删/权限变更 | 本地cron输出可能仍保留原文 |
| 浏览器无法访问微博 | 无需绕过访客系统，直接读本地文件 |
| 需要核对AI摘要的准确性 | 对比原始文本与摘要 |
| 历史内容回溯 | 按时间排序的markdown文件天然形成归档 |

## 日志查看

```bash
# 查看定时任务状态
hermes task list | grep 微博监控

# 手动执行测试
cd ~/.hermes/scripts && python3 weibo_monitor.py
```

## 相关参考文档

本技能吸收了以下专项知识的精华。每个文档保留了原始session的完整细节：

- `references/alternative-access.md` — 微博被封时的替代访问方案（知乎/B站/公众号等第三方平台）
- `references/hotsearch-scraper.md` — 微博热搜数据获取方法（浏览器工具/AKShare/聚合站）
- `references/debugging.md` — 监控脚本调试：重复推送根因、状态管理、静默机制、多副本陷阱
- `references/account-monitor.md` — 多账号监控配置、通知策略、随机延迟、Cookie管理
- `references/retweet-and-longtext-extraction.md` — 转发/长文微博的全文补抓方法
- `references/auto-tts-integration.md` — 语音播报集成方案