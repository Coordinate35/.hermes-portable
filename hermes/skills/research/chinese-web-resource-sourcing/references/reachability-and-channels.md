# 渠道可达性与资源流通样本（实测记录，随测随更）

> 最近一次实测：2026-09-13（VirtualBox Linux 客户机，无代理，中国网络）。
> **网络环境变化（挂代理 / 换网络）后重测本表并更新本文件。**

## 可达性（2026-09-13）

| 来源 | 状态 | 备注 |
|---|---|---|
| Anna's Archive | ❌ | 各域名不通 |
| Z-Library | ❌ | z-library.sk / 1lib.sk / z-lib.fm / z-lib.gs 等均不通 |
| LibGen | ❌ | .is / .rs / .li / .gs / .vg 全部不通 |
| Scribd | ❌ | 搜索结果里能看到，页面抓不到 |
| Google / Wikipedia | ❌ | 不通 |
| GitHub | ✅ | 可查线索（skill 仓库、issue），极少直接托书 |
| Bing | ✅ 站点通 | ⚠️ 裸 curl 搜中文会乱配到单字结果，别用 |
| 阿里云盘 | ✅ 页面通 | 下载仍要登录 |
| 苦瓜书盘 kgbook | ✅ | 文学/武侠为主；2025+ 新书基本搜不到（属正常） |
| 鸠摩搜书 | ⚠️ | 站点通，但 `init_hubs.php` / `ajax_fetch_hubs.php` 对非浏览器会话返回空（2026-05、2026-09 两次复验） |
| sobooks.cc | ⚠️ | 算术验证码（需同一 cookie 会话内先取题再提交答案），自动化易卡 |
| 书格 shuge.org | ✅ | 古籍为主 |

复测命令：

```bash
for u in https://annas-archive.org/ https://z-library.sk/ https://libgen.is/ https://www.kgbook.com/ https://www.jiumodiary.com/ https://github.com/; do
  echo -n "$u => "; curl -sI --max-time 6 -A "Mozilla/5.0" "$u" 2>&1 | head -1
done
```

## 资源流通形态样本（2026-09 实测）

- **夸克网盘打包**：azw3 + epub + mobi + pdf 全家桶，源头多为 TG 分享频道（如 @kaipanshare；t.me 本身不通），被 gying.click / gyingg.com 类聚合站转载——**多为 VIP 可见**；pan946.com 类论坛帖需注册 + 回复可见
- **公众号引流**：简书等平台发"每天分享一本书（附电子书）"，实际要关注公众号领取（样本："咚旭读书"）
- **付费论坛附件**：人大经济论坛类（注册 + 金币）
- **SEO 死链**：搜狐号等文章里的网盘链接多为死链（2026-09 实测某百度链返回"链接不存在"）
- **官方渠道**（微信读书 / 得到）：在线可读可听，但拿不到文件，进不了本地听书流程

## 历史实证

- **2026-09-07~08《货币强权》**（完整闭环）：so.com 快照挖到百度分享链 + 提取码（分享页验证存活）→ 用户自行取得 epub（z-lib 版）经 QQ 传入 → `add_book.py` 导入成功（74 章 / 248,402 字）
- **2026-09-13《如何快速了解一个行业》**（肖璟，2025-08 新书）：存量副本均卡账号墙（夸克打包 / 公众号引流 / 论坛注册帖），未发现公开直链——印证"新书只有登录墙后渠道"
