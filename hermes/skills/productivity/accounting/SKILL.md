---
name: accounting
description: 【个人记账·必加载】用户的个人记账系统已建立。任何涉及"支出/花费/记账/账单/花了多少/记一笔/这个月花/今天花/本周花/上个月花/消费/开销"等中文表达，都必须立即加载本 skill，不要询问用户数据在哪。数据已加密存于 ~/hermes_data/accounting/。AES-256-GCM 加密，按年切割，支持记录、删除、汇总。
---

# 加密记账系统

## 何时使用
- 用户说"记一笔 X 元 Y" → add
- "记错了，删掉刚才那笔" → delete (需二次确认)
- "本月/本周/今天花了多少" → summary
- "看看最近的支出" → find

## 核心文件
- 工具：`/home/coordinate35/hermes_data/accounting/accounting.py`
- 密钥：`~/.hermes/secrets/accounting.key` (绝不外泄、绝不进备份)
- 数据：`~/hermes_data/accounting/expenses_YYYY.jsonl.enc` (按年切割，逐行 AES-GCM 加密)
- 备份脱敏：`~/.hermes-portable/export.sh` 已配置 `--exclude='*.key' --exclude='secrets/'`

## 分类体系（固定，不要随意改动）
- **刚性**: 食 / 住 / 行 / 医
- **娱乐**: 餐饮娱乐 / 休闲 / 购物
- **成长**: 学习 / 健康 / 工具
- **其他**: 人情 / 杂项

判定原则：
- "外卖、买菜、水电、房租、地铁、看病" → 刚性
- "聚餐、奶茶、电影、游戏、旅游、衣服、数码" → 娱乐
- "书、课程、健身、营养品、效率工具" → 成长
- "礼物、红包、无法归类" → 其他

## 操作命令

### 1. 添加支出

**重要：始终使用 `/usr/bin/python3` 绝对路径**，因为用户的 `python3` 可能指向某个项目 venv（如 ebooks venv），那些 venv 通常没装 cryptography 会报 ModuleNotFoundError。系统 python3 已装好依赖。

```bash
# 当下记一笔（默认时间 = now）
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py add \
  --amount 35.5 --desc "午餐麦当劳" --cat 刚性 --sub 食 --note "可选备注"

# 补记历史支出（--when 可选，支持下列灵活格式）
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py add \
  --amount 35.5 --desc "午餐" --cat 刚性 --sub 食 --when "昨天中午"
```

**`--when` 支持的时间格式：**
- 相对日期: `今天` / `昨天` / `前天` / `大前天` / `3天前`
- 相对日期+时间: `昨天 14:30` / `昨天14点30` / `前天下午3点` / `今天早上9点`
- 时段词（自动映射）: `凌晨`(3) `早上/早晨`(8) `上午`(10) `中午`(12) `下午`(15) `傍晚`(18) `晚上`(20) `夜里`(22) `深夜`(23)
- 标准日期: `2026-05-13` (默认 12:00) / `2026-05-13 14:30` / `2026-05-13T14:30:00`
- 月-日（本年）: `05-13` / `5-13` (默认 12:00)

**重要：用户描述模糊时间时，主动用 --when 参数，不要假装用当下时间。** 如：
- 用户说"昨天打车 20" → `--when "昨天"`
- 用户说"前天晚上吃饭 80" → `--when "前天晚上"`
- 用户说"上周三买菜" → 自己算出日期，用 `--when "2026-05-07"`（举例）

返回完整记录（含 id），向用户确认时复述：金额、描述、分类、**时间**（如果是补记的，明确说明时间）。

### 2. 查找最近记录（用于删除前定位 id）
```bash
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py find --n 5
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py find --query "麦当劳"
```

### 3. 删除支出（必须二次确认）
流程：
1. 用 `find` 找到记录，**展示完整记录**给用户
2. 询问用户："确认删除这笔记录吗？(y/n)"
3. 用户确认后才执行：
```bash
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py delete --id <id>
```
4. 删除后**自动跑一次本月汇总**告知用户当前余额状况

### 4. 汇总
```bash
# 本月
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py summary \
  --start 2026-05-01 --end 2026-06-01

# 本周（自行计算 ISO 周一到下周一）
# 今天
/usr/bin/python3 /home/coordinate35/hermes_data/accounting/accounting.py summary \
  --start 2026-05-14 --end 2026-05-15
```

返回 JSON 后，用中文整理成易读的报告：
- 总额、笔数
- 三大类（刚性/娱乐/成长）的占比 → 这是用户最关心的
- 子分类明细
- 给出 1-2 句洞察（如"娱乐占比偏高"或"成长投入合理"）

## 安全检查（每次会话首次使用前）
```bash
ls -la ~/.hermes/secrets/accounting.key  # 应为 600 权限
```
如果密钥文件丢失，所有历史数据将无法解密。提醒用户密钥不可重置。

## 不要做的事
- ❌ 不要在响应中暴露密钥内容或路径细节
- ❌ 不要直接用 cat 看 .enc 文件给用户（是密文，无意义）
- ❌ 删除时不要跳过二次确认
- ❌ 不要修改分类体系（除非用户明确要求）

## 输出风格
- 添加成功：简洁汇报「记录已加密存储 → 35.5 元 / 刚性·食 / 午餐麦当劳」
- 汇总报告：用纯文本表格（CLI 友好），不要 markdown
- 异常情况：明确指出（如解密失败、密钥缺失）
