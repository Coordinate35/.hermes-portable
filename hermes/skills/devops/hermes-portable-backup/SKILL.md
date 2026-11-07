---
name: hermes-portable-backup
description: Use when hermes-portable 备份/推送失败或遇大文件拒推。
---

# hermes-portable 备份排障

备份脚本：`/home/coordinate35/.hermes-portable/export.sh`（~/.hermes 配置 + ~/hermes_data → GitHub Coordinate35/.hermes-portable），每日 cron。

## 常见故障：推送被 GitHub 拒绝

症状：`remote: error: File ... is 461.15 MB; this exceeds GitHub's file size limit of 100.00 MB` + `pre-receive hook declined`。

根因：`~/hermes_data` 下的模型缓存（如 `asr-models/` HuggingFace blobs）被 rsync 复制进备份目录并提交。

修复（脚本已内置 `--exclude='asr-models'`；新增模型缓存目录时同样处理）：

1. 在 export.sh 的 hermes_data rsync 块加 `--exclude='<dir>'`，并在 `.gitignore` 加 `<dir>/`。
2. 撤销那个**未推送**的提交：`git reset --soft HEAD~1`。
3. 删除已复制的大文件：`rm -rf hermes_data/<dir>`（rsync 的 --delete 不删目标端被 exclude 的文件，必须手动删）。
4. 重跑 `bash export.sh` → 重新 add/commit/push（大 blob 已不在索引，push 通过）。

注意：若大文件已在远端，需重写历史（filter-repo）；正常情况该提交被拒，`ahead 1` 即未推送，soft reset 即可。

## 验证

- `git log -1 --format='%H %ai'`
- `git ls-remote origin refs/heads/main` 与本地 HEAD 一致
- `git ls-files -z | xargs -0 ls -l | awk '$5>100000000'` 应为空

## 其他

- 脚本 `set -euo pipefail`，但 push 失败在内部 if 里被吞，退出码仍为 0 —— **不要只看 exit code，要 grep "Git 推送 ✓"**。
- GitHub 限制：单文件 100MB，仓库建议 < 1GB。
