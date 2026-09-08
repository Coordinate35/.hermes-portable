---
name: mindmap-rendering
description: Use when 用户要思维导图/mindmap/梳理成图。markmap为主，mermaid备选，含渲染坑位。
author: hermes-curator
category: creative
---

# 思维导图渲染（Mindmap Rendering）

把任意内容（读书笔记、框架、清单）渲染成 XMind 风格的思维导图图片。

## 触发条件

- 用户说"总结成思维导图 / 帮我做个 mindmap / 把 X 梳理成图 / 知识图谱"
- 已有 markdown 大纲（如读书笔记），需要转成可视化图

## 首选路线：markmap（XMind 风格，无连线穿框问题）

**为什么不是 mermaid mindmap**：mermaid mindmap（底层是 D3/ELK 布局）在节点多、文本长时**连线会穿过文本框、文字互相遮挡**（2026-09 实测用户反馈"图里面有一些遮挡"）。markmap 的斜线树状布局从节点边缘出线，无遮挡。

### 完整流程（全部本地化，已验证 2026-09-07）

```bash
mkdir -p ~/hermes_data/mindmaps && cd ~/hermes_data/mindmaps
npm init -y >/dev/null 2>&1
npm install --registry=https://registry.npmmirror.com markmap-cli
npx markmap-cli <大纲.md> -o out.html
```

### ⚠️ 三个必须修的坑（缺一不可，否则输出空白/错位）

1. **CDN 替换**：markmap-cli 生成的 HTML 引用 `https://cdn.jsdelivr.net/...`（d3、markmap-view、markmap-toolbar）。无代理环境直接打开 = 空白页。把 `src/href` 替换为本地 `node_modules/<pkg>/dist/...` 相对路径（d3.min.js、markmap-view/dist/browser/index.js、markmap-toolbar/dist/index.js、style.css）。
2. **补 fit()**：生成的 HTML **没有调用 `window.mm.fit()`**，内容默认渲染在视口角落（截图几乎全空白）。在 `window.mm = markmap.Markmap.create(...)` 之后加 `window.mm.fit();`。
3. **禁用动画**：`markmap.deriveOptions({ duration: 0, fitRatio: 0.95, initialExpandLevel: 3 })` 作为 create 第二参数，避免过渡动画干扰 headless 截图时机（initialExpandLevel 控制默认展开层数）。

### Chrome headless 截图（本机有 google-chrome 时的标准命令）

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --run-all-compositor-stages-before-draw --virtual-time-budget=15000 \
  --screenshot=out.png --window-size=3200,2400 --force-device-scale-factor=2 \
  "file:///path/to/out.html"
```

### 截图后必须验证（图可能"渲染成功但内容在角落/大片空白"）

视觉模型**全图判断不可靠**（本次 vision_analyze 全图把《货币强权》mindmap 误读为别的书——端侧降采样 + 幻觉），验证用程序化像素检查：

```bash
# 缩小 + 统计非白像素边界（内容 box）
ffmpeg -y -loglevel error -i out.png -vf scale=640:-1 -f rawvideo -pix_fmt rgb24 /tmp/small.raw
python3 -c "
data = open('/tmp/small.raw','rb').read()
w,h = 640,480; row = w*3; xs=[]; ys=[]
for y in range(h):
    for x in range(w):
        i = y*row + x*3
        r,g,b = data[i],data[i+1],data[i+2]
        if r<245 or g<245 or b<245: xs.append(x); ys.append(y)
print('content:', len(xs), 'box x', min(xs)*10, '-', max(xs)*10, ' y', min(ys)*10, '-', max(ys)*10)
"
```

- 内容 box 若明显偏离/偏小（如只占一个角落）→ 布局偏移，调整窗口尺寸重截。
- 内容有大量留白 → 用 ffmpeg crop 裁掉空白：`ffmpeg -y -i out.png -vf "crop=W:H:X:Y" final.png`（crop 不能原地覆盖输出同名文件）。
- 内容确认后，用 vision_analyze 的 **region 参数**抽查 2-3 个局部区域核对文字（region 是原图像素坐标 [x1,y1,x2,y2]），比全图 OCR 可靠。

### 大纲（markdown）写法

- `# 标题` = 根节点；`## 分支` / `- 要点` = 层级节点；缩进 = 层级。
- 节点文本里可以自由使用 `[ ] ( ) < > :` 等标点（与 mermaid 不同，无转义限制）。
- 中文、数字、`·`、`→`、`％` 都直接可用。
- 参考模板 `templates/mindmap-outline.md`。

## 备选路线：mermaid mindmap（当 markmap 不可用时）

```bash
# 安装（npmmirror 源）+ puppeteer 指向本地 chrome
cat > puppeteer-config.json <<'EOF'
{"executablePath": "/usr/bin/google-chrome",
 "args": ["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}
EOF
npx mmdc -i mindmap.mmd -o out.svg -p puppeteer-config.json
```

**语法陷阱（全实测，违反必炸）**：

1. **节点文本含 `[ ] ( ) { } < >` 会 Parse error，即使包在双引号里也一样**（mermaid 11.17 mindmap 解析器在引号内仍解析形状语法）。写法：`"没有方括号的内容"` 可过；`"[美]科恩"` 直接炸。
2. `root((题目<br/>副题))` 里 `<br/>` 也炸 → 根节点只用纯文本。
3. 含特殊字符的文本必须**净化**（删掉/汉字化所有 ASCII 括号、尖括号），不可依赖引号。
4. 解决排查技巧：把大文件逐个二分，每两行一组跑 `npx mmdc` 定位炸点（同类的 Parse error 都是特殊字符引起）。

**缺点（决定选型时的依据）**：节点 ~80+ 时连线穿框、文字重叠严重；仅适合节点少、文本短的简单图。

## 交付（QQ Bot）

- 发图片：回复里 `MEDIA:/abs/path/xxx.png` **独占整条回复**（与音频 MEDIA 铁律一致，避免渠道渲染器吞附件）。
- 尺寸建议 ≥ 4000px 宽（用户需点原图放大），底图无必要留白要 crop 掉。
- SVG 原件留在 `~/hermes_data/mindmaps/`，用户要"可编辑/高清版"时再给。

## 把图附进文档（用户会要求"附在笔记里"，2026-09 实测）

1. `cp 导出的图 ~/hermes_data/<书名>_思维导图.png`（与笔记同级，避免目录移动后引用失效）。
2. 在 markdown 笔记顶部插入：`![《书名》思维导图](书名_思维导图.png)`（**相对路径**，非绝对路径）。
3. 随笔记一起备份/移动即可，无需其他处理。

## 相关参考

- `references/mermaid-mindmap-pitfalls.md` — mermaid mindmap 语法坑的详细转录与排查过程（二分定位方法）。
- 用户书库/读书笔记源：`~/hermes_data/ebooks/<书名>/`，笔记 `~/hermes_data/<书名>_读书笔记.md`。

## 不要做的事

- ❌ 不要把 mermaid mindmap 当首选（遮挡问题被用户当场指出过）
- ❌ 不要直接用 markmap-cli 原生 HTML 截图（CDN 不可达 + 无 fit() = 空白）
- ❌ 不要用 vision_analyze 全图判断渲染对错（会幻觉），用像素 box + region 抽查
- ❌ 不要往 `~/` 根目录写工作文件（一律 `~/hermes_data/mindmaps/`）
