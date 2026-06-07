---
name: hermes-weixin-timeout-bug
description: Diagnose and workaround Hermes `Timeout context manager should be used inside a task` error in Weixin push.
triggers:
  - hermes weixin send failed
  - Timeout context manager should be used inside a task
  - cron job weixin push broken
---

# Hermes 微信跨事件循环 Bug 诊断

## 症状

- 当前对话通道正常（用户能收到回复）
- 但 cron job 或 `send_message` 工具调用时失败：
  ```
  Weixin send failed: Timeout context manager should be used inside a task
  ```

## 根因

`send_weixin_direct` 在 cron / `send_message` 调用时，通过 `_run_async` 在**新线程**中运行 `asyncio.run()`，创建了**全新的事件循环**。但 `live_adapter` 存在时，代码尝试复用绑定在 **gateway 主事件循环** 的 `_send_session`。aiohttp session 跨事件循环使用时，内部的 timeout context manager 检测到不在正确的 task 上下文中，抛出 `RuntimeError`。

## 检查

查看代码中已有的 weixin 相关修复：
- `5ca52bae`：分割 poll/send session，引入 `_LIVE_ADAPTERS` 重用 gateway 的 live adapter
- `e105b7ac`：iLink session 过期（-14）自动重试
- `8dcd08d8`：微信媒体上传修复
- `cedc95c1`：微信媒体 URL SSRF 校验

**目前无专门修复跨事件循环问题**（例如检测到当前 loop 与 session 绑定 loop 不一致时自动 fallback）。

## 临时 Workaround

**关闭 gateway 中的 weixin 连接**，让 cron / send_message 始终走独立 session fallback 路径，避免触发 live adapter 的跨 loop 问题。

## 彻底修复方向

在 `send_weixin_direct` 或 `_run_async` 中增加保护逻辑：
- 如果当前事件循环与 `_send_session` 绑定的事件循环不一致，**放弃复用 live_adapter session**，改为新建独立 session。

## 用户侧操作

1. `hermes update` 更新到最新版
2. 重启 Hermes 服务恢复通道
3. 如问题持续，临时关闭 gateway weixin 连接