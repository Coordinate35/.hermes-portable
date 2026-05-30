# 转发微博与长文全文提取

## 触发场景

`weibo_monitor.py` 抓回来的新微博 `text` 字段几乎是空的，或只含一个表情（如 `[祈祷]` / `[good]`）。
这通常意味着：

1. **该微博是纯转发** — 原作者本人只配了表情/单字，正文在 `retweeted_status` 里。
2. **该微博是长文** — `text` 字段被截断到 ~300 字符，末尾有"全文"链接。需要二次请求拿完整内容。

监控脚本只提取顶层 `text`，所以遇到上述两种情况，**必须额外抓一次原始 mblog 对象**才能向用户呈现有意义的内容。

## 复用脚本：fetch_mblog_full.py

skill 自带 `scripts/fetch_mblog_full.py`，用法：

```bash
cd ~/.hermes/scripts && PYTHONPATH=. python3 \
  /home/coordinate35/.hermes/skills/data-collection/weibo-monitoring/scripts/fetch_mblog_full.py \
  <uid> <weibo_id>
```

输出 JSON，字段：
- `text` — 顶层正文（去 HTML）
- `is_long_text` — bool
- `long_text` — 若 `isLongText=True`，已 follow `/statuses/extend?id=` 拿到的全文
- `retweet` — 若是转发，含 `{user, text, long_text, pic_urls}`
- `pic_urls` — 顶层附图 large url 列表

它直接 `import weibo_monitor as w` 复用 `HEADERS / COOKIES`，所以必须在 `~/.hermes/scripts/` 下运行（或 `PYTHONPATH` 指向它）。

## 关键 API 端点

| 用途 | URL | 来源字段 |
|:---|:---|:---|
| 用户时间线 | `https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&value={uid}&containerid=107603{uid}` | 已被 `weibo_monitor.fetch_weibo` 使用 |
| 单条详情 | `https://m.weibo.cn/statuses/show?id={mid}` | **会被反爬返回空** — 别依赖 |
| 长文全文 | `https://m.weibo.cn/statuses/extend?id={mid}` | 返回 `{data: {longTextContent: "..."}}` |

只用时间线 + extend 两个端点；`/statuses/show` 实测在当前 cookie 下返回 0 字节，不要浪费 token 重试。

## mblog 对象关键字段

```
id, mid, bid          # 三种 ID 表达
text                  # HTML，含表情 <img>；用 re.sub(r'<[^>]+>','',t) 去标签
raw_text              # 部分情况下有纯文本备份（如 '[祈祷]'）
isLongText            # True 时需调 /statuses/extend
pic_num, pics         # pics[*].large.url 是大图直链
retweeted_status      # 转发时的原微博完整 mblog 对象（递归同结构）
user.screen_name      # 原作者昵称
```

## 给 LLM 的呈现建议

发现新微博的 `text` 字段在去 HTML 后**只剩表情/<10 字符**时，必须：

1. 调 `fetch_mblog_full.py` 拿 `retweet` 字段；
2. 在回复里**明确标注"这是转发，本人只配了 X 表情"**，避免用户误以为是原创长文；
3. 转发原文逐字附上，禁止只发表情。

例如本人发"[祈祷]" + 转发 @某博主 万字长文，正确的回复结构：

```
@卢麒元 转发新动态：本人只配了 🙏

转发自 @某博主：
<完整原文>
```

## 反例（不要这么做）

- ❌ 只发 `[祈祷]` 给用户 — 信息量为零，用户不知道在祈祷什么
- ❌ 调 `https://m.weibo.cn/statuses/show?id=` 试图救场 — 返回空字节
- ❌ 用 `curl ... | python3 -c "..."` 解析 — 触发 tirith 安全扫描拦截，必须 `-o file` 再读
