---
name: hermes-channel-troubleshooting
description: "Use when 消息通道异常/不回消息. 先查通道→LLM API→会话，常见根因是内容风控污染会话。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, troubleshooting, gateway, qqbot, channel, diagnostics]
---

# Hermes 消息通道故障诊断

## When to Use

触发条件：用户报告某个平台/频道"聊天异常、发消息没反应、回复很慢、机器人不回话"等。

## 核心原则

- **通道"看似"异常 ≠ 通道故障**。多数情况下 WebSocket/平台连接是好的，问题在 LLM API 调用或会话状态。先做证据链，再下结论。
- **不要一上来就重启 gateway / 重建平台凭据**——这解决不了内容风控导致的会话污染。

## 诊断步骤（按顺序）

1. **确认 gateway 存活与平台连接**：
   - `ps aux | grep "hermes_cli.main gateway"` — gateway 进程在跑。
   - `python3 -c "import json; print(json.load(open('$HOME/.hermes/gateway_state.json'))['platforms'])"` — 各平台 state 应为 `connected`；`updated_at` 应为当前时间。
   - `tail ~/.hermes/logs/gateway.log` — 有无 `WebSocket connected / Reconnected / Session resumed` 及 `inbound message`（确认消息确实到达）。

2. **查 agent 侧错误（真正的根因所在）**：
   - `grep -E "Content|400|non-retryable|API call failed" ~/.hermes/logs/errors.log | tail -30`
   - 关键签名：`agent.conversation_loop: API call failed ... provider=custom base_url=... HTTP 400: xxx`、`Non-retryable client error`、`Streaming failed before delivery`、`Transient agent failure in session <id> — persisting user message`。
   - `400` 且 **non-retryable** = 模型提供方拒绝请求（如内容安全风控），不是网络/超时；重试无意义，每次消息都会再失败（响应耗时可能长达 5 分钟，如 `response ready: time=302.0s`）。

3. **定位被污染的内容（会话级）**：
   - 失败请求 dump 在 `~/.hermes/sessions/request_dump_<session_id>_<ts>.json`，结构：`{reason, error, request: {body: {messages: [...]}}}`。
   - 解析：逐层取 `d['request']['body']['messages']`（body 可能是 str 需再 json.loads）。
   - 扫描敏感词确认触发源（如 `grep -c '洗钱\|比特币\|黄金'`），常见来源：**历史 session_search 结果、memory-context 注入**——旧对话里的敏感主题（如反洗钱/金融犯罪术语、加密币话题）进入上下文后，让整个会话每次请求都命中内容安全过滤，即使只发"在线吗"。

4. **修复：重置被污染的会话**（无需重启 gateway）：
   - 备份：`hermes sessions export --session-id <id> --format md > ~/hermes_data/backup.md`（输出到 `~/.hermes/session-exports/`）。
   - 删除：`hermes sessions delete --yes <id>`（`--user <qq_id>` 的 archive 会命中全部历史会话，尽量按单个 session_id 精确操作）。
   - 验证：`hermes sessions list --chat-id <chat_id>` 确认旧会话消失；通知用户下一条消息会自动新建干净会话。
   - 若同会话再次触发：换模型（如 deepseek-v4-pro）可绕开该风控词表。

## Pitfalls

- 会话污染是**会话级**的：同 model 其他会话（如微信）可能完全正常，别据此误判整个 provider 挂掉。
- 设备状态 `state.db-wal` 变大、`sessions.json` 有 stale entry 是正常现象（gateway 会自动 dropping stale entry and recovering），不必处理。
- `500字以内`/`QQ Bot 短句走语音` 等回复策略与故障诊断无关，诊断时不混入。
- 用户消息会被 gateway 持久化以备重试（`persisting user message so conversation context is preserved on retry`），删除会话后这些消息随会话消失，属预期。

## References

- `references/content-risk-session-case.md` — 2026-09-02 完整案例：QQ Bot"聊天异常"实为 DeepSeek 400 Content Exists Risk 会话污染，含日志时间线、dump 解析命令与修复命令。
