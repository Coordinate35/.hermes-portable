---
title: 微博监控脚本调试与防重复推送
description: 微博API监控中遇到的重复推送问题及解决方案，包含状态管理、时间比对、API特性等关键知识点
tags: [微博, 监控, 去重, 状态管理, API, 调试]
name: weibo-monitoring-debugging
version: 1.0.0
---

# 微博监控脚本调试与防重复推送

## 问题背景

使用微博移动API (`m.weibo.cn/api/container/getIndex`) 监控特定账号新微博时，出现**重复推送**问题：同一条微博被多次推送。

## 微博API关键特性

### 1. 返回顺序非时间顺序
```
API返回顺序示例：
  [0] 14:07 - 回复别人的评论
  [1] 13:42 - 原创微博
  [2] 13:24 - 原创微博
  ...
```
**陷阱**：不能直接用 `weibos[0]` 作为最新微博，必须按 `created_at` 排序。

### 2. 只返回最近10条
- API限制：最多返回10条最近微博
- 如果账号10分钟内发了11条，第11条将不可见
- 下次检查时，如果中间有遗漏，会误判旧微博为新微博

### 3. 时间格式
```python
# 格式: "Fri Apr 24 13:42:33 +0800 2026"
datetime.strptime(time_str, '%a %b %d %H:%M:%S +0800 %Y')
```

## 重复推送的根本原因

### 原因1：时间倒退（主要问题）

**场景**：
```
第1次运行：
  API返回: [14:07, 13:42, ...]
  排序后最新: 14:07
  推送: 14:07
  保存: last_time = 14:07 ✓

第2次运行（API窗口变化）：
  API返回: [13:42, ...]  ← 14:07不在列表中！
  排序后最新: 13:42
  保存: last_time = 13:42 ✗ ← 时间倒退！

第3次运行：
  API返回: [14:07, 13:42, ...]
  14:07 > 13:42 → 被认为是"新"微博
  → 重复推送！
```

**解决方案**：保存状态时取最大值，防止倒退
```python
current_last_time = parse_weibo_time(last_time_str) if last_time_str else datetime.min
if latest_time >= current_last_time:
    save_time = latest_time_str
else:
    save_time = last_time_str  # 保持原值，防止倒退
```

### 原因2：时间精度问题

微博时间只精确到秒，如果1秒内发多条，可能出现：
- 时间相同但ID不同
- 时间比较 `>` 会漏掉相同时间的

**解决方案**：使用 `>=` 或结合ID比对

### 原因3：原创 vs 回复

- 原创微博：正常时间
- 回复评论：也是一条微博，时间可能晚于原创
- 转发：也是一条微博

**陷阱**：不能把回复误认为新原创内容

## 正确的检测逻辑

```python
def check_new_weibos(weibos, last_time_str):
    """
    weibos: API返回的微博列表（未排序）
    last_time_str: 上次记录的最新时间
    """
    # 1. 按时间排序（新→旧）
    sorted_weibos = sorted(
        weibos, 
        key=lambda w: parse_time(w['created_at']), 
        reverse=True
    )
    
    # 2. 解析上次时间
    last_time = parse_time(last_time_str) if last_time_str else datetime.min
    
    # 3. 收集新微博（时间 > last_time）
    new_weibos = []
    for w in sorted_weibos:
        w_time = parse_time(w['created_at'])
        if w_time > last_time:  # 严格大于
            new_weibos.append(w)
        else:
            break  # 按时间倒序，遇到旧的就停止
    
    return new_weibos, sorted_weibos[0]  # 返回新列表+最新微博
```

## 状态管理最佳实践

### 状态文件完整结构
```json
{
  "user_id": {
    "last_id": "1234567890",
    "last_time": "Fri Apr 24 14:07:27 +0800 2026",
    "pushed_ids": ["id1", "id2", "id3", "id4", "id5"],
    "last_check": "2026-04-24T14:07:30",
    "user": "用户名"
  }
}
```

**pushed_ids 的作用**：
- 记录API返回的**所有**微博ID（不仅仅是已推送的）
- 当API窗口变化时，防止旧微博被误判为新微博
- 保留最近的 15-20 个ID即可（防止无限增长）

### 更新状态时的防倒退逻辑
```python
# 读取当前状态
current_last_time = parse_time(state[uid].get('last_time', ''))

# API返回的最新时间
latest_time = parse_time(latest_weibo['created_at'])

# 取较大值，防止倒退
if latest_time >= current_last_time:
    save_id = latest_id
    save_time = latest_time_str
else:
    # API可能遗漏了更新的微博
    save_id = last_id
    save_time = last_time_str

# 更新状态
state[uid] = {
    'last_id': save_id,
    'last_time': save_time,
    'last_check': datetime.now().isoformat()
}
```

## 额外的防重复措施

### 方案A：记录已推送ID集合
```python
# 状态文件中增加
"pushed_ids": ["id1", "id2", "id3"]  # 最近10条

# 推送前检查
if weibo_id in state[uid]['pushed_ids']:
    skip()  # 已推送过
```

### 方案B：写入前备份
```python
import shutil

def save_state(state, filepath):
    # 备份旧状态
    if os.path.exists(filepath):
        shutil.copy2(filepath, f"{filepath}.backup")
    
    # 写入新状态
    with open(filepath, 'w') as f:
        json.dump(state, f)
```

### 方案C：文件锁（多进程场景）
```python
import fcntl

def save_state_atomic(state, filepath):
    with open(filepath, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # 独占锁
        json.dump(state, f)
        fcntl.flock(f, fcntl.LOCK_UN)  # 释放锁
```

---

## Cron Job 静默机制问题（2026-04-30）

### 问题现象
明明没有新微博，但 cron job 每 5 分钟给用户发一条消息，内容是 LLM 对"脚本正常运行但无输出"的解释。

### 根本原因

**Cron job 的静默规则**：
- 脚本 stdout 有内容 → 交给 LLM 处理，LLM 输出会发送给用户
- 脚本 stdout 为空 → 交给 LLM 处理，**LLM 应该输出 `[SILENT]`**

**陷阱**：LLM 不总是严格遵守 `[SILENT]` 规则。当脚本 stdout 为空时，LLM 可能"自由发挥"，输出类似：

> "脚本已成功执行，无输出内容。运行状态：包装脚本正常完成..."

这会被当成正式消息推送给用户。

### 复现条件
1. 包装脚本在无新微博时 `return 0` 且 stdout 为空
2. Cron job prompt 中声明了 `[SILENT]` 规则
3. LLM 没有严格遵守该规则

### 解决方案

**让包装脚本主动输出 `[SILENT]`，不依赖 LLM 的行为：**

```python
# 包装脚本 weibo_monitor_wrapper.py

# 检查实际监控脚本的 stdout
stdout_content = result.stdout.strip()

if stdout_content:
    # 有新微博或错误消息 → 输出内容
    print(stdout_content)
else:
    # 无新微博 → 主动输出 [SILENT]，不留给 LLM 发挥空间
    print("[SILENT]")
```

### 为什么这个方案可靠

| 方案 | 依赖对象 | 风险 |
|-----|---------|-----|
| 空 stdout + 期望 LLM 静默 | LLM 遵守规则 | ❌ 不可靠 |
| 脚本主动输出 `[SILENT]` | 脚本逻辑 | ✅ 确定性 |

### 检查方法

查看 cron job 输出目录，统计非 `[SILENT]` 的空运行：
```bash
# 统计 4月29日 晚间的非静默运行次数
for f in ~/.hermes/cron/output/JOB_ID/2026-04-29_*.md; do
    tail -n 1 "$f" | grep -v '^\[SILENT\]$'
done | wc -l
```

如果数字 > 0，说明存在静默机制失效问题。

### 修复步骤
1. 修改包装脚本，在"无新微博"分支主动 `print("[SILENT]")`
2. 确保实际监控脚本（`weibo_monitor.py`）在无新微博时 stdout 为空
3. 验证：运行包装脚本，检查输出是否为 `[SILENT]` 或有新微博内容

### 关键教训
> 不要依赖 LLM 遵守 `[SILENT]` 规则。Cron job 的静默应该是**脚本层面的确定性行为**，而不是对 LLM 行为的期望。

---

## 调试技巧

### 1. 添加详细日志
```python
print(f"[DEBUG] API返回 {len(weibos)} 条微博")
print(f"[DEBUG] 本地 last_time: {last_time_str}")
print(f"[DEBUG] API最新: {latest_time_str}")
print(f"[DEBUG] 新微博数: {len(new_weibos)}")
```

### 2. 模拟运行
```python
# 不修改状态文件，只打印检测逻辑
python3 weibo_monitor.py --dry-run
```

### 3. 状态文件版本控制
```python
# 保存历史状态，便于追溯
import time
backup_file = f"state_{int(time.time())}.json"
shutil.copy2(STATE_FILE, backup_file)
```

## 常见问题排查

| 现象 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 重复推送 | 时间倒退 | 添加防倒退逻辑 |
| 漏推送 | API只返回10条 | 缩短检查间隔 |
| 大量历史推送 | last_id不在API窗口 | 首次运行标记 |
| 时间解析错误 | 格式不匹配 | 添加异常处理 |

## 推荐方案组合

**必须实施的防护措施**：
1. 按时间排序API返回
2. **记录所有看到的微博ID（不仅仅是新推送的）**
3. 状态更新时防止时间倒退
4. **确保只有一个脚本副本**

**可选增强措施**：
1. 状态文件备份
2. 多进程文件锁

---

> ⚠️ **核心要点**：微博API返回非时间顺序 + 窗口限制(10条) + 状态倒退 = 重复推送。必须防倒退 + ID去重双重保障。

---

## 实战调试案例（2026-04-25）

### 问题现象
定时任务每5分钟运行，但同一条微博被重复推送多次。

### 调试过程

#### 1. 检查脚本副本
```bash
find /home/coordinate35 -name "weibo_monitor.py" -type f
```
发现 **4个副本**：
- `~/.hermes/scripts/weibo_monitor.py` ← 修复的版本
- `~/.hermes/hermes-agent/weibo_monitor.py` ← 定时任务实际使用的版本（旧版）
- `~/.hermes/skills/.../weibo_monitor.py` ← 旧版
- `~/hermes_data/weibo_monitor.py` ← 旧版

#### 2. 核心问题：状态文件被旧版本破坏
旧版本保存状态时会**丢失 `pushed_ids` 和 `last_time` 字段**，导致：
- 时间倒退检查失败
- ID去重失效

#### 3. 解决方案：双重防护

**第一重：记录所有看到的ID**
```python
# 原来只记录新推送的ID，现在记录API返回的所有ID
account_weibo_ids = [str(w['id']) for w in sorted_weibos]  # 所有看到的
account_new_ids = [str(w['id']) for w in new_weibos if w['uid'] == uid]  # 真正新的

# 合并去重
pushed_ids = account_new_ids + [pid for pid in pushed_ids if pid not in account_new_ids]
pushed_ids = pushed_ids + [wid for wid in account_weibo_ids if wid not in pushed_ids]
pushed_ids = pushed_ids[:MAX_PUSHED_IDS]  # 保留最近20个
```

**第二重：防止时间倒退**
```python
current_last_time = parse_weibo_time(last_time_str) if last_time_str else datetime.min
if latest_time >= current_last_time:
    save_id, save_time = latest_id, latest_time_str
else:
    # API可能遗漏了更新的微博，保持原来的
    save_id, save_time = last_id, last_time_str
```

#### 4. 最终修复步骤
1. 统一脚本版本：将修复版复制到定时任务使用的路径
2. 删除多余副本：只保留一个脚本文件
3. 修复状态文件：重新写入完整的 `pushed_ids` 列表

### 实际效果
- 状态文件正常更新 `pushed_ids` 和 `last_time`
- 不再有重复推送
- 新微博能正常检测

### 关键教训
1. **多副本陷阱**：修复脚本时必须确认定时任务使用的是哪个路径
2. **状态字段完整性**：旧版本可能破坏状态文件结构，需要手动修复
3. **双重防护策略**：单纯依赖时间比对不可靠，必须结合ID去重

### 推荐的脚本结构
```
~/.hermes/
├── hermes-agent/
│   └── weibo_monitor.py          # 唯一脚本文件
├── scripts/
│   └── (empty - 删除多余副本)
└── cron/
    └── output/                    # 定时任务输出

~/hermes_data/weibo_data/
├── last_weibo.json              # 状态文件
└── new_weibo_*.txt              # 推送记录
```