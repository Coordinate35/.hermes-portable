# 微博监控自动语音播报 — 实施记录

## 背景

用户通过 QQ Bot 接收微博监控推送，并希望每次新微博都附带一段语音播报。

## 对 weibo_monitor.py 的修改

### 步骤1：添加 subprocess 导入

```python
import subprocess  # 新增，用于调用 curl 生成语音
```

### 步骤2：在新微博输出前插入 TTS 生成

定位到 `if new_weibos:` 块，在 `print(result)` 之前插入：

```python
        # 收集语音文本
        voice_texts = []
        for w in new_weibos:
            output.append(format_weibo(w))
            voice_texts.append(f"{w['user']}发布新微博：{w['text']}")
        
        # ... 保存文件 ...
        
        # 生成语音播报
        try:
            voice_text = '。'.join(voice_texts)
            voice_path = f"/tmp/weibo_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            payload = json.dumps({"text": voice_text, "text_language": "zh"}, ensure_ascii=False)
            tts_result = subprocess.run(
                ['curl', '-s', '-X', 'POST', 'http://192.168.56.1:9880',
                 '-H', 'Content-Type: application/json',
                 '-d', payload,
                 '-o', voice_path, '--connect-timeout', '10'],
                capture_output=True, text=True, timeout=20
            )
            if tts_result.returncode == 0 and os.path.exists(voice_path) and os.path.getsize(voice_path) > 1000:
                result += f"\nMEDIA:{voice_path}"
        except Exception:
            pass  # 语音生成失败则忽略，仅发送文字
```

### 关键细节

- `voice_text` 中使用 `。` 连接多条微博，避免语音合成时句子过长或连接不自然
- `–connect-timeout 10` + `timeout=20` 确保不阻塞主流程
- `–s` 式 curl 避免进度条污染 stdout
- 文件大小检查 `> 1000` bytes 排除空/损坏文件
- 任何异常都被捕获，降级为纯文字推送

## Cronjob Prompt 更新

必须在 cronjob prompt 中明确指示 agent 保留 MEDIA: 标记：

```
核心规则：
1. 脚本输出为空或 [SILENT] → 无新微博，请回复 "暂无新微博"并结束
2. 脚本输出包含 "🚀 微博监控" → 有新微博
3. 如果输出中包含 "MEDIA:/path/to/file.wav" 标记，
   **必须原样保留在你的回复中**，不能删除或修改
4. 对新微博内容做简单总结，然后附上完整原文和 MEDIA: 标记

重要：
- MEDIA: 标记是语音文件路径，必须原样输出，否则语音无法发送
- 不要对微博内容做过多解读，以原文为主
```

## 推送目标切换

### 从微信切换到 QQ

```bash
hermes cronjob update a27ae1b5f602 --deliver qqbot
```

### 从 QQ 切换到微信

```bash
hermes cronjob update a27ae1b5f602 --deliver weixin
```

### 验证

```bash
hermes cronjob list
# 确认 deliver 字段为目标平台
```

## 常见问题

### MEDIA: 标记被 agent 误删

征像：用户反馈“有文字但没有语音”

根因：Cron job agent 的 prompt 未明确要求保留 MEDIA: 行，或 agent 误以为是内部标记而删除。

修复：在 cronjob prompt 中加入显式指令（见上文模板）。

### TTS 请求超时

征像：文字推送正常，但没有语音文件

根因：TTS 服务未启动、网络不可达、或文本过长导致合成超时。

排查：
```bash
curl -X POST "http://192.168.56.1:9880" \
  -H "Content-Type: application/json" \
  -d '{"text":"测试","text_language":"zh"}' \
  --output /tmp/test.wav --connect-timeout 10
```
