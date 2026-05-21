# QQ Bot 语音播报工作流

Session: 2026-05-21

## 完整流程

从华尔街见闻 API 获取头条 → 生成语音文本 → 调用 TTS 服务 → 推送语音到 QQ Bot。

### 1. 获取头条

```bash
curl -s "https://api-one-wscn.awtmt.com/apiv1/content/carousel/information-flow?channel=global&limit=8"
```

解析时注意 `item.resource` 嵌套结构，不是顶层字段。

### 2. 生成语音文本

将头条整合为连续语音文本，添加序号和开场/结束语：

```
华尔街见闻今日头条。第1条，...。第2条，...。以上是华尔街见闻今日头条。
```

### 3. 调用 TTS

优先使用用户的 Windows 宿主机本地 TTS 服务（GPT-SoVITS V2）：

```bash
curl -X POST "http://192.168.56.1:9880" \
  -H "Content-Type: application/json" \
  -d '{"text":"播报内容","text_language":"zh"}' \
  --output /tmp/output.wav
```

注意：使用 `cat` 或 `$(cat file)` 传递长文本时需要注意 shell 转义。建议直接在 Python 脚本中构造 JSON。

### 4. 发送语音

Hermes 中使用 `MEDIA:/path/to/file.wav` 格式发送。

## 常见坑

- **shell JSON 转义**：用 `$(cat file)` 传递含有中文标点的文本时，bash 会尝试解析特殊字符（如 `、` 等）。建议在 Python 中构造请求。
- **API 结构**：carousel API 的文章在 `item.resource` 下，不是顶层。
- **TTS 文本过长**：本地 TTS 服务对超长文本可能分段处理不当，建议提前分段或摘要。
