---
title: Weibo Account Monitor
description: 监控指定微博账号的新内容，支持多账号、失败重试、智能通知策略
author: Hermes
name: weibo-account-monitor
---

# Weibo Account Monitor

监控多个微博账号的新内容，只在有新微博或连续多次失败时才通知用户。

## 使用场景

- 监控投资大V的微博动态
- 跟踪特定账号的内容更新
- 避免频繁收到"无新内容"的打扰

## 配置参数

```yaml
accounts:
  - name: "账号昵称"
    uid: "1234567890"
  - name: "第二个账号"
    uid: "0987654321"

check_interval: 5  # 分钟
cron_schedule: "*/5 * * * *"

# 通知策略
notify_on_new: true           # 有新微博时通知
notify_on_failure: 3          # 连续N次失败才通知（设为0则立即通知）
silent_on_normal: true        # 正常运行时静默

# 随机延迟（避免固定时间被反爬）
random_delay: true            # 启用0-60秒随机延迟
```

## 文件结构

```
/home/coordinate35/hermes_data/weibo_data/
├── last_weibo.json          # 状态追踪文件
├── backup_YYYYMMDD_HHMMSS.txt    # 手动备份文件
└── new_weibo_YYYYMMDD_HHMMSS.txt # 自动备份新微博

~/.hermes/scripts/
└── weibo_monitor.py         # 监控脚本
```

## 状态文件格式

```json
{
  "account_uid": {
    "last_id": "最新微博ID",
    "last_time": "Mon Jan 01 12:00:00 +0800 2024",
    "last_check": "2024-01-01T12:00:00",
    "user": "账号名称"
  },
  "failures": {
    "account_uid_fail_count": 0
  }
}
```

**关键字段说明**：
- `last_id`: 最新微博的ID（用于显示）
- `last_time`: 最新微博的发布时间（核心：用于时间比对检测）
- `last_check`: 上次检查时间（ISO格式）

## Cron任务管理

```bash
# 添加任务
hermes cronjob add --name="微博监控-卢麒元" --schedule="*/5 * * * *" --command="python3 ~/.hermes/scripts/weibo_monitor.py"

# 查看任务
hermes cronjob list

# 删除任务
hermes cronjob remove <job_id>
```

## 依赖

- Python 3.x
- 需要有效的Weibo Cookie（SUB, SUBP等）
- requests, random, json, datetime, os, sys

## 注意事项

1. **Cookie有效性**：Weibo Cookie会过期，需要定期更新
2. **API限制**：m.weibo.cn有访问频率限制，避免过于频繁
3. **数据隐私**：Cookie包含敏感信息，注意保护
4. **状态持久化**：失败计数器保存在状态文件中，重启后保持

## 已知陷阱 (Pitfalls)

### 1. API返回顺序 ≠ 时间顺序
**⚠️ 重要**：微博API返回的卡片列表**不是按发布时间排序的**！

实际观察到的现象：
- 第1条卡片可能是置顶微博（几天前的）
- 第2条可能是昨天的微博  
- 第3条才是今天最新发布的微博
- 回复/评论类微博可能插在前面

**错误做法**（会导致漏检新微博）：
```python
# ❌ 不要直接取第一个卡片
cards = data.get('data', {}).get('cards', [])
first_card = cards[0]  # 这不一定是最新的！
```

**正确做法**（已在脚本中实现）：
```python
# ✅ 获取所有卡片后按时间排序
weibos = []
for card in cards:
    if card.get('card_type') == 9:
        # 收集所有微博...
        weibos.append({...})

# 按created_at排序
sorted_weibos = sorted(weibos, key=lambda w: parse_weibo_time(w['created_at']), reverse=True)
latest = sorted_weibos[0]  # 这才是最新的
```

### 2. API只返回最近10条微博 + 时间比对检测
**🚨 极关键**：微博API每次只返回最近的约10条微博！

如果监控间隔较长（如5小时以上）或者账号发布频繁，可能会遇到：
```
保存的last_id: 第11条微博（不在API返回中）
API返回: [第1条, 第2条, ..., 第10条]  
```

**历史问题**：
```python
# ❌ 错误的检测逻辑（会导致历史微博轰炸）
if last_id:
    for w in sorted_weibos:
        if str(w['id']) == last_id_str:
            break
        new_weibos.append(w)  # 如果last_id不在列表中，全部10条都会被标记为新微博！
```

**正确做法** — 时间比对（推荐）：
```python
# ✅ 时间比对：记录 last_id + last_time，按时间检测多条新微博
state[uid] = {
    'last_id': latest_id,
    'last_time': latest_time_str,  # 新增：记录发布时间
    'last_check': datetime.now().isoformat(),
    'user': name
}

# 检测逻辑：所有时间比 last_time 新的都算新微博
last_time = parse_weibo_time(last_time_str)
for w in sorted_weibos:  # 按时间倒序
    w_time = parse_weibo_time(w['created_at'])
    if w_time > last_time:
        new_weibos.append(w)
    else:
        break  # 时间倒序，遇到旧的就停
```

**优势**：
- 可同时检测多条新微博（用户一次发多条时不会漏）
- 不受ID是否在当前10条窗口内的限制
- 不会因last_id过期而误报历史微博

### 3. 时间倒退陷阱（Timestamp Regression）
**🚨 重复推送的根源**：API窗口不稳定导致 `last_time` 倒退

**场景重现**：
```
时间线：  13:42(原创) ←→ 14:07(回复)

第1次运行：
  - API返回: [14:07, 13:42, ...]
  - 推送: 14:07
  - 保存: last_time = 14:07 ✓

第2次运行（14:07被API遗漏）：
  - API返回: [13:42, ...]  ← 14:07不在列表中！
  - 推送: 无 (13:42 < 14:07)
  - 保存: last_time = 13:42 ✗ ← 时间倒退！

第3次运行（14:07又出现了）：
  - API返回: [14:07, 13:42, ...]
  - 推送: 14:07（被当成"新"微博）
  - 保存: last_time = 14:07
→ 14:07 被重复推送！
```

**错误做法**（会导致重复推送）：
```python
# ❌ 直接用sorted_weibos[0]更新时间，可能导致倒退
state[uid] = {
    'last_time': latest_time_str,  # 如果API遗漏最新微博，这里会倒退
}
```

**正确做法** — 防止倒退：
```python
# ✅ 保存状态时取最大值，防止时间倒退
current_last_time = parse_weibo_time(last_time_str) if last_time_str else datetime.min

# 更新last_time时，取当前值和新值的最大值
if latest_time > current_last_time:
    new_last_time_str = latest_time_str
    new_last_id = latest_id
else:
    new_last_time_str = last_time_str  # 保持原值，不倒退
    new_last_id = last_id

state[uid] = {
    'last_id': new_last_id,
    'last_time': new_last_time_str,
    'last_check': datetime.now().isoformat(),
    'user': name
}
```

**核心原则**：
- `last_time` 只能前进，不能倒退
- 只有当 `latest_time > current_last_time` 时才更新
- 这保证了即使API窗口波动，也不会重复推送

## 扩展

可修改脚本支持：
- 微信/邮件通知
- 关键词过滤
- 图片/视频下载
- 情感分析
