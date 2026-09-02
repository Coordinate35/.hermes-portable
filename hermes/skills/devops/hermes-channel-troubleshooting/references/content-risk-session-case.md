# 案例：QQ Bot"聊天异常" = DeepSeek 400 Content Exists Risk 会话污染（2026-09-02）

## 现象

用户报告"qq bot 的聊天异常了"。实际表现：QQ Bot 发"在线吗"后 5 分钟无响应（`response ready: time=302.0s`），多次同样失败。

## 证据链（日志时间线）

- `gateway_state.json`：qqbot `state=connected`，`updated_at` 为最新 —— 通道没问题。
- `gateway.log`：22:32:25 `WebSocket connected` / `Ready, session_id=...`；22:32:35 `C2C message ... content='在线吗'` —— 消息到达正常。
- `errors.log`（真正的根因）：
  - 21:44:53 / 21:46:08 / 21:46:22 / 21:48:36 / 22:37:37 全部：`agent.conversation_loop: API call failed (attempt 1/3) error_type=BadRequestError ... provider=custom base_url=https://api.deepseek.com model=deepseek-v4-flash-vision-exp summary=HTTP 400: Content Exists Risk`
  - 21:44:53: `Non-retryable client error: Error code: 400 - {'message': 'Content Exists Risk', 'type': 'invalid_request_error'}`
  - 22:37:37: `Streaming failed before delivery` + `Transient agent failure in session 20260902_110432_39266111 — persisting user message so conversation context is preserved on retry.`
- 同一会话 21:44-22:37 之间**每次**请求（"在线吗"）都失败 → 会话级污染，重试无效。

## 触发源确认（request dump 解析）

文件：`~/.hermes/sessions/request_dump_20260902_110432_39266111_20260902_223737_513738.json`

结构：`{timestamp, session_id, reason: "non_retryable_client_error", error, request: {method, url, headers, body}}`；`body` 是字符串需再 `json.loads` 一次；`body.messages` 为对话数组。

解析命令：
```python
import json
d = json.load(open('request_dump_<sid>_<ts>.json'))
body = d['request']['body']
if isinstance(body, str): body = json.loads(body)
msgs = body['messages']
for m in msgs: print(m['role'], str(m.get('content'))[:100])
```

命中内容：早期 `session_search` 工具结果把旧对话全文带进了上下文——其中包含 "smurfing / 拆分交易规避反洗钱报告 / 100 万美元拆 1000 次每次 9900 美元 / 联邦重罪 31 U.S.C. § 5324"（洗钱术语 2 处、比特币 66 处、黄金 83 处）。DeepSeek 内容安全过滤因此拒绝整个会话的每次请求。

## 修复命令

```bash
hermes sessions export --session-id 20260902_110432_39266111 --format md > ~/hermes_data/qqbot_session_backup.md
hermes sessions delete --yes 20260902_110432_39266111
hermes sessions list --chat-id 4E42EA828928C02FC47FEB6334392F69 --limit 3   # 确认旧会话消失
```

- 不要用 `--user <id>` 的 archive（会命中该用户全部历史会话，95 个）。
- 不需要重启 gateway；下一条消息自动新建干净会话。
- 备份默认输出到 `~/.hermes/session-exports/<sid>-session.md`。

## 结论要点

- 通道正常 ≠ 无故障：故障在 LLM 提供方的内容安全过滤，且是**会话级、不可重试、永久复发**（直到重置会话）。
- 用户上报"聊天异常"时先查 `errors.log` 的 `non-retryable client error`，这是最快定位路径。
