# 新闻获取 + 语音合成集成模式

将华尔街见闻头条（或其他新闻源）合成为语音播报的完整工作流。

## 使用场景

用户要求"念一下头条"、"语音播报新闻"、"把新闻读给我听"等。

## 完整流程

### 1. 获取新闻

调用华尔街见闻 carousel/headlines API：

```bash
curl -s "https://api-one-wscn.awtmt.com/apiv1/content/carousel/information-flow?channel=global&limit=10"
```

解析响应结构（注意 `item.resource` 嵌套）：
```json
{
  "data": {
    "items": [
      {
        "resource_type": "article",
        "resource": {
          "title": "...",
          "content_short": "...",
          "author": {"display_name": "..."},
          "display_time": 1234567890
        }
      }
    ]
  }
}
```

### 2. 构建语音文本

拼接为适合语音播报的格式：

```
华尔街见闻今日头条。
第1条，{标题}，{摘要前60字}。
第2条，{标题}，{摘要前60字}。
...
以上是华尔街见闻今日头条。
```

**注意**：
- 去掉原文中的 `"` 等可能导致 JSON 转义失败的字符
- 控制总长度在 TTS 服务限制内（通常 ≤2000 字符）
- 保留 `text_language: "zh"` 参数

### 3. 语音合成

优先使用用户的本地 TTS 服务（参见 `tts-orchestration` skill）：

```bash
curl -X POST "http://192.168.56.1:9880" \
  -H "Content-Type: application/json" \
  -d '{"text":"拼接后的播报文本","text_language":"zh"}' \
  --output /tmp/news_tts.wav
```

### 4. 同时交付

- **音频**：`MEDIA:/tmp/news_tts.wav`
- **文字摘要**：Markdown 格式的头条列表（供用户快速浏览）

## 已知问题

- carousel API 返回的 `content_short` 可能包含全角省略号 `…`，在 f-string 中需特殊处理
- `display_time` 是 Unix 时间戳（秒），需用 `datetime.fromtimestamp()` 转换
- 合成超长文本时，优先服务可能超时或失败，需准备好降级链

## 示例会话

用户："念一下现在的华尔街见闻头条"

→ 获取 carousel API top 5
→ 拼接语音文本（约 500-800 字符）
→ POST 到 192.168.56.1:9880
→ 返回 WAV 音频 + 文字摘要
