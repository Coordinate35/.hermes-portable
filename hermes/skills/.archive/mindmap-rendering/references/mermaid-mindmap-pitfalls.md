# mermaid mindmap 语法坑（2026-09-07 实测）

环境：`@mermaid-js/mermaid-cli@11.17.0`（mermaid v11），node v22，本机 google-chrome 147，npm 走 npmmirror。
首次失败命令：`npx mmdc -i mindmap.mmd -o out.png -p puppeteer-config.json`

## 现象与根因

```
Error: Parse error on line 4:
... "书籍信息"      "[美]本杰明·J.科恩 著"    ...
Expecting 'SPACELINE', 'NL', 'EOF', got 'NODE_ID'
```

- ✅ `"带引号的节点"` / `root(货币强权)` / `"张琦 等译"`（纯中文引号节点）都能过
- ❌ `root((《货币强权》<br/>副题))` —— 双圆括号 root 中 `<br/>` 触发 Parse error
- ❌ `"[美]科恩"` —— **引号内的 `[` 仍触发 Parse error**（引号不豁免方括号/圆括号/尖括号）

结论：mermaid mindmap 11 的文本解析器即使在双引号内也解析 `[ ] ( ) { } < >` 为形状语法。
**规则：mindmap 节点文本必须净化所有 ASCII 括号/尖括号，不能依赖引号。**

## 最小复现（验证我判断的二分流程）

```bash
# 每 2-3 行一组写成临时 .mmd，跑 npx mmdc，报错的行=炸点
printf 'mindmap\n  root(货币强权)\n    "书籍信息"\n      "[美]科恩"\n' > t.mmd
npx mmdc -i t.mmd -o t.png -p puppeteer-config.json   # 炸
printf 'mindmap\n  root(货币强权)\n    "书籍信息"\n' > t4.mmd   # 过
```

## 其他注意

- mindmap 图尺寸由布局决定；`-w/-H` 只改视口，不改字体大小；要高清用 `-o .svg` + chrome 渲染，或 `-s N`。
- 渲染 SVG 后 viewBox 即内容尺寸（本次 2897×1172），chrome 打开纯 SVG 时内容固定左上 1x，需 `--window-size=viewBox尺寸 --force-device-scale-factor=2` 才放满放大。
- 节点 80+ 时连线穿过文本框（用户反馈"有遮挡"）→ 换 markmap。
