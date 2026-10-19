---
name: chinese-web-resource-sourcing
description: 找书/找中文资源卡在网盘登录墙时用：so.com快照挖链+用户回传闭环。
version: 1.0.0
author: Hermes Curator
category: research
license: MIT
metadata:
  hermes:
    tags: [Research, Chinese-Web, Netdisk, Ebooks, Sourcing, Fallback]
    related_skills: [audiobook-reader, blocked-page-recovery]
---

# 中文资源找源（网盘链接挖掘与登录墙兜底）

场景：要找某个中文资源（以电子书为主），但所有直接渠道都够不到。核心事实先说：

**国内新资源（尤其 2025+ 新出版书）的可下载副本只走网盘（夸克、阿里云盘、百度为主），免登录直链基本不存在。能不能拿到文件，取决于：能不能挖到公开分享链接，或者用户自己的渠道。**

完整的听书管道（导入/切章/朗读/进度）属于用户自有技能 `audiobook-reader`；本技能只管「把源找出来 / 拿回来」这一段，两者配合使用。渠道可达性与样本见 `references/reachability-and-channels.md`。

## When to Use（触发条件）

- 找书 / 下载电子书 / 找 XX 资源 / 求 epub、mobi、pdf
- 网盘链接 / 提取码 / 夸克网盘 / 百度网盘 / 阿里云盘 / 直链
- "帮我找到电子版 / 为什么下载不了 / 链接失效了"

## 技法一：so.com（360搜索）快照挖链【两次会话验证】

1. so.com 搜组合词：`"<书名>" 网盘` / `"<书名>" 提取码` / `"<书名>" epub 下载`
   - 贴吧/知道的"求物帖"被快照收录时，**摘要文本里直接带 pan 链接 + 提取码**（实证 2026-09：《货币强权》的有效百度链+提取码即从摘要文本挖出）
2. **结果页每条结果带 `data-mdurl="<真实URL>"`** —— 直接 grep 出目标站真地址，绕过 `/link?m=` 跳转包装（实证拿到过 jianshu / bilibili / sohu 真 URL）
3. 挖到的分享链接**必须验活**：curl 分享页看标题，"链接不存在 / 分享已过期" = 死链；SEO 垃圾站（搜狐号等）转发多为死链
4. 反例：裸 curl `cn.bing.com` 搜中文会乱配到单字（白费轮次）；搜狗微信 `/link` 跳转对无 JS 自动化空响应

快捷探测脚本（单站 curl，可直接跑）：

```bash
bash scripts/mine_links.sh "<关键词>"
```

等价手写命令：

```bash
curl -sG --max-time 15 "https://www.so.com/s" --data-urlencode "q=<关键词>" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept-Language: zh-CN,zh;q=0.9" -o /tmp/so.html
# 网盘链接 + 提取码
grep -oE '(pan\.(baidu|quark)\.(com|cn)[A-Za-z0-9/_.?=-]{4,}|alipan\.com/s/[A-Za-z0-9]+|aliyundrive\.com/s/[A-Za-z0-9]+|提取码[:：]?[ ]?[a-z0-9]{4})' /tmp/so.html | sort -u
# 结果真 URL
grep -oE 'data-mdurl="[^"]+"' /tmp/so.html | sed 's/data-mdurl="//; s/"$//' | sort -u
```

## 技法二：渠道可达性快检（一次批量跑，别逐个试）

```bash
for u in https://annas-archive.org/ https://z-library.sk/ https://libgen.is/ https://www.kgbook.com/ https://www.jiumodiary.com/ https://github.com/; do
  echo -n "$u => "; curl -sI --max-time 6 -A "Mozilla/5.0" "$u" 2>&1 | head -1
done
```

最近一次实测结论与样本渠道见 `references/reachability-and-channels.md`。**网络环境变化（挂代理/换网络）后重测并更新该文件。**

## 技法三（终局）：登录墙 → "用户回传文件"闭环【已验证】

当公开渠道全卡账号墙（夸克/阿里云盘打包、论坛注册帖、公众号引流、付费论坛附件——**本机无网盘账号，跨不过去，别硬刚、别擅自注册账号**）：

1. 把能公开拿到的入口全部挖出来（网盘链接+提取码 / 帖子地址 / 页面 URL）
2. **回报用户**：说明现状 + 给可用入口；用户一般能自行取到文件（先例 2026-09：用户自行从 z-lib 取得 epub，经 QQ 发来文件）
3. 用户发来文件后交给下游流程（听书：`add_book.py --source <文件> --title "<书名>" --version "..."` → 完整性核查）
4. 全程不要未经用户批准注册第三方论坛/网盘账号；不硬刚验证码

## ⚠️ 抓取命令被 BLOCK 的处置（2026-09 实测）

多站批量抓取链、验证码流程、复杂组合命令可能触发运行时审批；无人应答即超时返回 `BLOCKED: ... user has NOT consented`。简单单站命令一般能过。被 BLOCK 后：

1. **不重试 / 不改写 / 不换工具重放同一命令**（系统明确禁止，重放必再被拒）
2. 本地已下载文件改用 `read_file` / `search_files` 等非 terminal 工具检查
3. 确需继续时拆成更小的单站命令再试
4. 属流程必需步骤 → 停下向用户说明，等确认

## 不要做的事

- ❌ 不要为绕过账号墙擅自注册论坛/网盘账号（先问用户）
- ❌ 不要把死链 / SEO 垃圾转发当作可用入口给用户（先验活）
- ❌ 不要被 BLOCK 后重试同一命令
- ❌ 不要用裸 curl cn.bing.com 搜中文；不要反复调鸠摩搜书 API
- ❌ 不要承诺"一定能下到"——新书大概率只有登录墙后的渠道，兜底是用户回传
