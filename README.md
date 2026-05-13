# Hermes Agent 跨机器同步备份

本仓库用于将 Hermes Agent 的完整配置、人格、记忆、技能和全息记忆数据库备份到 GitHub，实现跨机器同步恢复。

## 仓库结构

```
hermes-portable/
├── hermes/                  # ~/.hermes 的关键配置
│   ├── SOUL.md              # 人格定义
│   ├── config.yaml          # 主配置（API Key 已脱敏）
│   ├── memories/            # 记忆文件
│   ├── skills/              # 技能库
│   ├── cron/jobs.json       # 定时任务配置
│   ├── scripts/             # 自定义脚本
│   └── memory_store_core.sql # 全息记忆数据库（文本导出，无 BLOB 向量）
├── hermes_data/             # ~/hermes_data 用户数据
├── scripts/
│   └── rebuild_vectors.py   # HRR 向量重建脚本
├── export.sh                # 导出脚本（当前机器 → 本仓库）
├── import.sh                # 导入脚本（本仓库 → 新机器）
└── .gitignore
```

## 快速开始

### 当前机器：首次导出

```bash
cd ~/.hermes-portable
./export.sh

# 配置 GitHub 远程仓库（首次）
git remote add origin https://github.com/YOUR_USER/hermes-portable.git
git branch -M main
git push -u origin main
```

### 新机器：恢复

```bash
# 1. 安装 Hermes Agent（先完成官方安装流程）

# 2. Clone 本仓库
git clone https://github.com/YOUR_USER/hermes-portable.git ~/.hermes-portable

# 3. 运行导入脚本
cd ~/.hermes-portable && ./import.sh

# 4. 编辑 ~/.hermes/config.yaml，填入你的 API Key

# 5. 启动 Hermes Agent
```

## 核心设计决策

### 为什么不用 `*.db.gz`？

SQLite `.db` 是二进制文件，gzip 压缩后 Git 无法做 delta。任何微小改动都会让整个 `.gz` 完全不同。每天备份会让仓库按 ~240MB/天的速度膨胀。

### 为什么不用含 `hrr_vector` 的 `sqlite3 .dump`？

`hrr_vector` 是二进制向量（每条事实 ~8KB BLOB），dump 后变成十六进制字符串，导致 dump 达 ~488MB，其中 97% 是伪随机十六进制，Git delta 完全失效。

### 正确方案：排除 BLOB 列的全量 SQL dump

排除 `hrr_vector` 后，全量 dump 仅 ~17MB（实际文本 ~7MB），Git delta 非常高效。恢复后通过 `rebuild_all_vectors()` 从内容重新计算向量。

| 指标 | 含 hrr_vector | **不含 hrr_vector** |
|:---|:---:|:---:|
| 工作区文件 | 488MB | **~17MB** |
| Git 初始 pack | 276MB | **~6MB** |
| 每天 10 条增量 | ~275MB | **~50KB** |
| 30 天后 gc | 262MB | **~7MB** |
| 一年总量 | 100GB | **~20MB** |

## 自动备份

通过 Hermes Agent 的 cron 系统，每天 03:00 自动执行 `export.sh`。

## 注意事项

1. **必须是私有仓库** — 即使脱敏了，配置信息仍推荐保密
2. **恢复后必须重建 HRR 向量** — `import.sh` 已自动包含此步骤
3. **state.db 不备份** — 会话历史是临时日志，新机器重新开始更干净
4. **hermes_data 中的 venv/ 不备份** — Python 虚拟环境可重建
