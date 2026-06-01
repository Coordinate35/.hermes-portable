---
name: audiobook-reader
description: 【听书系统·必加载】用户的电子书听读系统。涉及"找书/下载书/导入书/加新书/读书/继续读/听到哪了/跳到第X回/书库"等请求，或任何朗读电子书相关场景，必须先加载本 skill。封装了书库管理、格式解析(epub/txt/mobi/pdf)、章节切分、按段朗读、进度记忆、TTS集成的完整链路。
author: coordinate35
category: media
---

# 听书系统（Audiobook Reader）

用户的个人电子书听读系统。所有书按书名隔离管理，支持任意格式输入（统一解析为章节化纯文本），按段朗读，自动记忆进度，支持多本书并行进度。

## 触发条件（命中任意一条立即加载本 skill）

⚠️ **以下所有条件地位平等，不存在"可选"与"强制"的区分。命中即执行，禁止自行排优先级。**

### 1. 书库查询类
- "书库里有什么 / 我有哪些书 / 现在书库里有哪些书 / 当前有哪些书 / 听书系统里有什么"
- "列出所有书 / 列一下我的书 / 看一下书单"
- "有什么书可以听 / 能听什么 / 我下载了什么书"
- → 调 `library.py list`

### 2. 进度查询类
- "听到哪了 / 我听到哪了 / 现在听到哪了 / 听到第几回了"
- "当前进度 / XX的进度 / XX听到哪了"
- "上次听到哪 / 我读到哪 / 这本书看到哪"
- "今天听了多少 / 进度怎么样"
- → 调 `library.py progress --book "<书名>"`（若有多本书需先列出让用户选）

### 3. 添加书类
- "找书/下载书/导入书/加新书/添加XX到书库/把XX加进来"
- "买XX的电子书"（用户语境是要听的）
- → 走下载流程 + `add_book.py`

### 4. 朗读类
- "读XX/朗读XX/念XX/给我读XX/听XX"（XX 是书名或"继续"）
- "继续读 / 继续读N段 / 接着念 / 接着读 / 再念几段"
- "跳到第X回 / 从第X回开始 / 重新开始读 / 回到上一段"
- "这一回讲什么 / 当前章节摘要 / 总结一下这章"
- → 调 `read.py`，再走 TTS 链路

### 5. 删除/管理类
- "删除XX / 把XX从书库去掉 / 不要XX了"
- → 调 `library.py remove --book "<书名>"`

### 自检问题
「用户的请求是否涉及：电子书、书库、章节、朗读、听书、进度？」
- 是 → 必须先加载本 skill
- 否 → 忽略

## 接到需求时的对齐流程（动手前必做）

用户偏好"先思考权衡 → 呈现方案 → 确认后再执行"，听书任务尤其要先对齐以下参数，**不要默认值假设就开干**：

| 维度 | 默认推断 | 必须确认的场景 |
|---|---|---|
| 版本 | 优先三联修订版（金庸类） | 用户没明说版本时问一下；找不到指定版本要先回报、给降级选项（如新修版） |
| 格式 | epub > txt > 其他 | 若只有 txt 等格式可得，提示用户切分质量可能下降 |
| 朗读模式 | B（5 段连读） | 第一次为某本书启动朗读时确认连读段数 |
| 章节定位 | 从 progress.json 接着读 | 用户说"重新开始/跳到 X"时显式 locate，不要默默重置进度 |
| 下载渠道 | 见 `references/book_sources.md` 实测列表 | 渠道全挂时停下来回报，不要凭直觉去试墙外站浪费时间 |
| **版本标注** | **任何导入必须 `--version` 字段写清版本** | 用户多次强调"标明是新修版/三联版"，导入时不写版本是硬错误，会被立刻指出 |

**反例**（曾犯）：用户只说"下载射雕"，未确认就开始去 Anna's Archive 试三个域全挂，然后又试 zlib 全挂，最后才找到苦瓜书盘——浪费了 5+ 个工具调用。**正确做法**：先看 `references/book_sources.md` 的实测优先级，按可达列表第一个试。

**反例 2**：找到非目标版本（如想要三联版只有新修版）时，**必须先回报给用户**，给"先用此版跑通 vs 继续找目标版"两条路让用户选，不要默默用替代版导入。

## 系统约定

### 目录结构
```
~/hermes_data/ebooks/
├── library.json                # 全局书库索引
├── <书名>/
│   ├── source.<ext>            # 原始文件
│   ├── meta.json               # 元数据
│   ├── chapters.json           # 章节索引
│   ├── chapters/NNN.txt        # 章节纯文本
│   ├── progress.json           # 进度
│   └── audio_cache/            # TTS 音频缓存
```

### 关键默认值
| 项 | 默认值 |
|---|---|
| 默认连读段数 | **5 段** |
| 段落长度目标 | 300-500 字 |
| 短段合并阈值 | < 50 字 |
| 长段切分阈值 | > 500 字（按句号切） |
| 默认朗读模式 | B（段落连读，可指定段数） |
| 并行进度 | 支持，按书隔离 |
| 已支持格式 | epub, txt, mobi |
| 待补格式 | pdf（遇到时再补 parsers/） |

## 核心命令

所有脚本在 `~/.hermes/skills/media/audiobook-reader/scripts/` 下。

### 1. 添加书 / 导入书
```bash
python3 ~/.hermes/skills/media/audiobook-reader/scripts/add_book.py \
  --source <本地文件路径或URL> \
  --title "<书名>" \
  [--author "<作者>"] [--version "<版本>"]
```
- 自动识别格式（按扩展名）
- 解析、切章、建索引、写 meta.json
- 完成后报告：总章节数、总字数

### 2. 朗读（核心入口）
```bash
python3 ~/.hermes/skills/media/audiobook-reader/scripts/read.py \
  --book "<书名>" \
  [--mode continue|chapter|locate] \
  [--chapter N] [--paragraph N] [--count 5]
```
- `--mode continue`：从 progress.json 接着读（默认 5 段）
- `--mode chapter`：读整章（输出多个音频片段）
- `--mode locate`：跳到指定章节/段落，更新进度，然后读
- **输出**：JSON 到 stdout，结构 `{audio_files: [...], texts: [...], chapter: N, paragraph_range: [a,b], total_progress: "X.X%"}`
- **TTS 不在此脚本内调**，本脚本只产出文本片段；TTS 由 agent 层按 voice-message-delivery skill 走降级链

### 3. 书库管理
```bash
python3 ~/.hermes/skills/media/audiobook-reader/scripts/library.py list
python3 ~/.hermes/skills/media/audiobook-reader/scripts/library.py info --book "<书名>"
python3 ~/.hermes/skills/media/audiobook-reader/scripts/library.py progress --book "<书名>"
python3 ~/.hermes/skills/media/audiobook-reader/scripts/library.py remove --book "<书名>"
```

## 导入后必做：完整性核查（曾被用户当场要求）

**触发**：每次 `add_book.py` 跑完，**不要立刻宣布"导入完成"**。先跑完整性核查再回报。

用户偏好：会主动核验我的工作（"你先统计下字数，看看完整性是否符合预期"），不做核查就上报是被指出的高频问题。

**核查项目**（用 `scripts/verify_book.py` 一次性跑完）：

1. **总字数 vs 公认基准** — 比如金庸射雕约 80 万汉字，明显偏少/偏多要解释
2. **章节字数分布** — 找出 `< 平均 0.5×` 的异常短章节，定位是切分错误还是真实差异
3. **末段完整性** — 每章最后一段应以 `。！？"…` 收尾，否则疑似被截断
4. **章节标题完整性** — `chapters.json` 章数对得上预期（如金庸修订版固定 40 回 + 后记 + 附录×2 = 43）
5. **重复章节侦测** — 相邻两章标题/首句高度相似时报警（**mobi 解析常见 bug**：同一章被切成两个条目，会让总章数虚高）
6. **HTML 噪音残留** — 每章末尾 grep 站名/版权关键词（如"金庸""版权""官网"）
7. **跨版本对比**（如果同书有多版） — 同回字数差 > 30% 时标红，确认是真实修订还是数据缺失

**对外回报模板**：

```
📊 完整性核查报告
✅ 总章节: N（预期 N）
✅ 汉字数: XXX,XXX（行业基准约 XX 万）
⚠️ 异常项: <列出来 + 解释>
🟡 已知小问题: <列出来 + 修复成本估计>
结论: 可用 / 需修复
```

**反例**（本会话犯过）：
- 新修版 mobi 导入显示 41 章，**实际是 mobi 把第 37 章重复成第 38 章**。如果当时跑了"相邻章标题相似度"核查，会立刻发现，而不是等到用户对比两版字数时才暴露。
- 三联版每章末尾都有孤立"金庸"两字（站方版权署名残留），TTS 念到末段会多读"金庸"。**应该在 import 前的 crawler 阶段加进 skip_keywords**，而不是 import 后再回补。

详细的核查脚本和判定阈值见 `scripts/verify_book.py` 和 `references/completeness_checklist.md`。

## Agent 层使用流程（重要）

### 书名别名与“继续”的当前书解析

用户常用简称说“继续念射雕/继续”，但书库目录名可能带版本后缀（如 `射雕英雄传（三联修订版）`），直接把简称传给 `read.py --book` 会报“书不存在”。处理顺序：

1. 本会话已有上一条成功听书 MEDIA → 继续用同一本书的**完整书库标题**。
2. 用户只给简称（如“射雕英雄传/射雕”）且精确标题不存在 → 先用 `library.py list` 查书库，找包含该简称的标题。
3. 匹配多本同书不同版本时 → 优先沿用最近一次朗读的版本；若无会话上下文，优先选 `progress.json.last_read_at` 最新且进度最靠后的版本；仍不确定才问用户。
4. 一旦解析出完整标题，后续 `read.py` / `precompose.py` / `synth_batch.py` 全部使用完整标题，避免缓存路径和进度错位。

read.py 只产出**文本片段**，不直接合成语音。Agent 必须：

1. 调 `read.py` 拿到段落文本数组（默认 5 段）
2. **将所有段落文本拼成一个字符串**（段间用 `\n\n` 分隔，让 TTS 有自然停顿），**一次性**送给 TTS 合成 **一条** 音频
   - 输出文件名约定：`combined_ch<NNN>_p<MMM>-p<KKK>.wav`，**闭区间**，MMM 是第一段 index，KKK 是最后一段 index。⚠️ `read.py` 的 `paragraph_range` 是半开区间 `[start, end)`，agent 层构造文件名时要用 `p{start}-p{end-1}`，确保和 `precompose.py` 输出一致
   - 路径：`~/hermes_data/ebooks/<书名>/audio_cache/`
3. TTS 走 voice-message-delivery 降级链：
   - 先 `bash ~/.hermes/scripts/win_tts.sh "<拼接后的全文>" <out_path>`
   - 失败 → MeloTTS
   - 再失败 → `edge-tts` CLI
4. **字符上限保护**：拼接后 > 2500 字时，自动 fallback 到"分批 TTS + ffmpeg concat"（见 voice-message-delivery skill 的长文本处理章节）。≤ 2500 字直接一次合成。
5. 按平台规则交付：QQ Bot 用 `MEDIA:<path>` 独占一条回复，**整批 5 段就发 1 条**
6. read.py 已自动更新 progress.json，不需要 agent 再写

### ⚠️ QQ Bot 听书交付的铁律（统一规范，覆盖之前所有"半放行"版本）

**这条回复必须是有且仅有 `MEDIA:<绝对路径>` 一行，前后上下不能有任何字符。**

不允许的"加一点点文字"包括（但不限于）：

- 章节标题（如"第一回 风雪惊变"）
- 进度百分比（如"段220-224，进度3.09%"）
- 剧情概括（如"—— 包惜弱半推半就入秀水客栈"）
- 章节末庆祝 emoji（如"🎉 第一回完结"）
- 下一回预告（"下一回是「江南七怪」"）
- 已知 bug 提示（如"末尾可能有'金庸'两字残留"）
- 任何 emoji、标点装饰

**唯一例外**：用户**主动问**了具体信息（"听到哪了"、"这一回讲什么"、"刚刚那段什么意思"），那条回复整条就是纯文字回答、**完全不带 MEDIA**——即先停下播放，回答完再等用户说"继续"。

**根因**：QQ Bot 渠道下，`MEDIA:` 与同条文字共存时，渠道渲染器可能把整条当文字处理、吞掉音频附件，用户只看到文字、收不到音频。这是用户在 2026-05 射雕会话**当场指出**的——"你刚刚把文字和语音消息混在一起了，第一回最后一段语音消息没发过来"。

**read.py 返回的 chapter / chapter_title / paragraph_range / total_progress_pct 字段**是给 agent 自己用的（构造缓存文件名、判断章节末尾、决定预合成位置），**不是给用户的播报字幕**。看到这些字段不要顺手往用户回复里塞。

**正确格式（唯一）**：

```
MEDIA:/home/coordinate35/hermes_data/ebooks/<书名>/audio_cache/combined_ch001_p220-p224.wav
```

**全部错误格式**（任意一种都会让 QQ Bot 丢音频）：

```
❌ 一行标签 + MEDIA：
第一回 风雪惊变（段220-224，进度3.09%）
MEDIA:/path/to/x.wav

❌ 章节末 emoji + 总结 + MEDIA：
🎉 第一回 风雪惊变 完结（进度3.09%）—— 包惜弱入秀水客栈
MEDIA:/path/to/x.wav

❌ 多段叙述 + 提示 + MEDIA：
第一回 风雪惊变完结。下一回是江南七怪。提示：末尾有"金庸"残留。
MEDIA:/path/to/x.wav
```

**自检（每次发 MEDIA 前问自己）**：这条 assistant 回复里 `MEDIA:` 行之外**还有任何一个字符**吗？有 → 删掉、或拆成下一条回复发。

**真的有必要告诉用户的事**（如三联版章末"金庸"噪音、章节切换、版本问题）→ 起**下一条独立文字回复**发，不要塞同一条。听书是沉浸式连续接收，文字注解是例外。

详细的 MEDIA 投递规则、其它平台行为、为什么 QQ Bot 会吞 MEDIA，见 `voice-message-delivery` skill 的「平台感知消息规则（QQ Bot）」章节。

### 为什么"整批拼接一次合成"是默认（v2 升级，2026-05）

| 方案 | 用户体验 | 语调连贯 | TTS 次数 | 选择 |
|------|---------|---------|---------|------|
| ❌ 旧：5 段分别合成 5 条音频 | 用户要点 5 次播放 | 段间有 prosody 断点 | 5 次 | 弃用 |
| ✅ 新：5 段拼一起一次合成 1 条 | 点一次听完 | 全段连贯朗读 | 1 次 | 默认 |

**铁律**：除非超 2500 字阈值触发 fallback，**绝不**再回到"分段分发多条 MEDIA"的旧做法。这是用户明确确认过的偏好。

### 缓存复用

合成前先检查 `combined_ch<NNN>_p<MMM>-p<KKK>.wav` 是否已存在且 size > 10KB，存在则直接复用，不再调 TTS。

### 音频缓存的自动清理（运维约定）

所有听书音频（每本书的 `audio_cache/*.wav`）已经被纳入全局的 `~/.hermes/scripts/tts_audio_cleanup.sh`，由 cronjob `tts-audio-cleanup`（每天凌晨 3:00，no_agent 模式）自动删除 **7 天前**的文件。

清理命令的关键参数（**改的时候不要破坏它**）：

```bash
find ~/hermes_data/ebooks -mindepth 3 -type f -name "*.wav" -mtime +7 -delete
```

- `-mindepth 3` 是必须的——保证只删 `ebooks/<book>/audio_cache/<file>` 层（深度 3），不会误删上层的 `meta.json` / `chapters.json` / `library.json`。
- 通配符 `*` 自动覆盖任何新加入书库的书，**新增书无需改清理脚本**。
- 保留期 7 天和其他 TTS 音频一致；用户偏好统一策略，不要给听书单独设更长保留期。

### 音频缓存的备份排除（`~/.hermes-portable/export.sh`）

听书 `audio_cache/` 目录**不进每日 GitHub 备份**——可重建、体积大、变化频繁。export.sh 的 rsync 段已加 `--exclude='audio_cache'`。

**⚠️ rsync exclude 模式匹配陷阱（曾被踩坑）**：

rsync 的 `--exclude='cache'` **不会**匹配 `audio_cache` 目录。pattern 默认是 **完整文件名/目录名匹配**，不是子串匹配。所以 export.sh 里早就有的 `--exclude='cache'` 救不了 `audio_cache`，必须单独加一条 `--exclude='audio_cache'`。

测试验证方法（任何排除规则改动后跑一次）：

```bash
SRC_DATA="$HOME/hermes_data"
rsync -anv --exclude='audio_cache' "$SRC_DATA/ebooks/" /tmp/rsync_test/ 2>&1 \
  | grep -E '(audio_cache|\.wav)' | head -5
# 期望：空输出。有任何匹配 = 规则失效。
```

**和 `voice-message-delivery` skill 的关系**：那个 skill 的"音频文件清理"章节给的命令只覆盖 `/tmp` 和 `~/.hermes/audio_cache`，不包含书库音频。**这里是补充扩展，不是替代**。如果有人问"音频在哪、怎么清理"，先回答这一段（书库 wav 的路径和清理规则），再引用 voice-message-delivery 处理 TTS 临时文件。

### 🚀 后台预合成（v3 升级，2026-05）

**目标**：用户说"继续"时，下一批音频已经预合成好，直接发缓存，**0 等待**。

**铁律**：每次发完当前批 wav 之后，**必须**立即在后台启动一次"下一批预合成"。**这不是可选项**。

#### 实现方式

发完当前 MEDIA 后，开启 background terminal 跑：

```bash
source ~/hermes_data/ebooks/.venv/bin/activate && \
python3 ~/.hermes/skills/media/audiobook-reader/scripts/precompose.py \
  --book "<书名>" --peek-offset 0 --count 5
```

参数说明：
- `--peek-offset 0`：合成"从当前 progress 位置开始的下一批"。
- `precompose.py` 内部用 `read.py --peek` 取段、不动 progress

**起后台进程时**：用 `background=true`，**不需要** `notify_on_complete=true`（预合成完成是隐式的，下次"继续"时检查文件是否存在即可，不需要主动通知）。

#### ⚠️ peek-offset 的正确语义（曾被踩坑）

时序很关键，offset 是相对 **progress 当前值**而非"我刚发完的那批"：

```
T0: progress=p5（用户即将听 p5-9）
T1: agent 调 read.py continue           → 取 p5-9，progress 推进到 p10
T2: agent 用 win_tts 合成 p5-9 的 wav 并发 MEDIA
T3: agent 启动后台预合成下一批
     ↑ 此时 progress=p10，"下一批"= p10-14
     ↑ 所以应该用 --peek-offset 0（"当前批 = 用户还没听的下一批"）
     ❌ 错误：用 --peek-offset 1 会预合成 p15-19，跳过 p10-14
```

**铁律**：每次调用顺序是 `read.py continue` → 发 MEDIA → `precompose --peek-offset 0`。如果有人改成 `offset=1` 会导致用户每次"继续"都缓存未命中、临时合成、等待 5-10 秒。

**反例（本会话犯过）**：第一次给"继续"功能用 `--peek-offset 1` 预合成了 p10-14，结果用户说"继续"时实际要的是 p5-9（progress 当时还在 p5），缓存未命中。改成 `--peek-offset 0` 后正常。

**反例 2（第二次又犯过）**：把"先 continue 推进 → 再发 MEDIA → 再 precompose offset=0"这条流程的**第一步和第三步顺序搞反**了——在还没调 `read.py continue` 之前就启动了 `precompose --peek-offset 0`，结果预合成的是"用户本批要听的内容"（因为 progress 还没推进），等用户说"继续"后 `read.py continue` 把 progress 推到下下批，预合成的那个文件名匹配不上，缓存未命中。

⚠️ **铁律重申**：每次"继续"的完整顺序：

```
1. read.py --mode continue --count 5         # 先推进 progress（不可省、不可移到后面）
2. ls 检查 combined_chXXX_pYYY-pZZZ.wav      # 上一轮的预合成应已就绪
3. 启动 precompose --peek-offset 0 后台      # 为下一次"继续"准备
4. 发 MEDIA: 行（独占一条回复）
```

第 3 步和第 4 步顺序无所谓，但 **绝不能** 把 `precompose` 放到 `read.py continue` 之前——progress 没动时 offset=0 就是"用户本批"，做完是白做工。

### 跨章节边界的章末"金庸"噪音段处理

三联版每回末尾有一个孤立"金庸"段（站方版权署名残留，详见上文「导入后必做」章节）。这段在 progress 里**正常占一个段位**，会造成两类边界场景：

**场景 A：continue 刚好把"金庸"段塞进本批**（少见，需要 count 偏大或起点近章末）：
拼接文本里会有孤立的"金庸"二字，TTS 念出来。用户听到末尾突然冒出"金庸"。

**场景 B：continue 在"金庸"段之前一段结束**：
read.py 算出 `end_idx == len(paragraphs) - 1`，仍认为本章未结束，**下次 continue 会单独读出"金庸"那一段**——拼接出来就是一条只念"金庸"两字的 2 秒短音频。

**agent 层规避（强制）**：
- 跨章边界的补播 / 单段播放前，**先 peek 这段内容**，strip 后若 ≤ 5 个汉字且无标点（命中"金庸/古龙/梁羽生"等署名模式），**直接 skip + 把 progress 推进过去，不发 MEDIA**。
- 章末 progress 自动跳到下一章（`next_chapter` +1，`next_paragraph=0`）时，**不要假设"漏了一段要补"**。先确认上一章的 `paragraph_count` 与最后一次 continue 的起点关系，多半是正常章末跳转。

**反例（本会话踩过）**：发现 progress 从第二回跳到第三回 p0，直觉判断"漏了第二回 p210 没念"，手动 locate 取出来才发现是孤立"金庸"署名段，险些当作正文音频补播给用户。

### 章末跳转 vs 真 bug 的快速判断

看到 `next_chapter` 突然 +1、`next_paragraph=0` 时按这个序排查，不要瞎补播：

```bash
python3 -c "
import json
ch = json.load(open('/home/coordinate35/hermes_data/ebooks/<书名>/chapters.json'))
print('上一章段数:', ch[<chapter-1>-1]['paragraph_count'])
"
# 若 last_continue_start + count >= 上一章段数 → 正常章末跳转，无需补播
# 否则 → 真的漏段，去查 progress.json 历史
```

#### ⚠️ 启动预合成必须是独立后台进程，绝不能与 read.py 串联

**禁止**这种写法：

```bash
# ❌ 错的：read.py 在 background 里先跑，把 progress 推到 p120，然后 precompose 合成 p120-124
# 但用户当前要听的是 p115-119，下次"继续"时缓存未命中
background: read.py continue --count 5 > out.json && precompose --peek-offset 0
```

**正确顺序**（每次"继续"的标准动作）：

1. **前台**调 `read.py --mode continue --count 5` 推进 progress（同步等返回，拿到当前批的 paragraph_range）
2. **前台**检查/合成当前批 wav（命中缓存直接用，否则现场合成）
3. **独立后台**进程跑 `precompose.py --peek-offset 0`（此时 progress 已是下一批起点，所以 offset 0 = 用户下次"继续"要的那批）
4. 发 MEDIA

把 read.py 放到 background 里和 precompose 串联，会让"progress 推进"和"预合成"在同一时间窗里发生，逻辑上等价于 `--peek-offset 1`，必然每次都未命中。

**根因**：`--peek-offset 0` 的"0"是相对**调用 precompose 时刻**的 progress 值。read.py 先跑就会把这个基准向前推一格，offset 0 就变成"再下一批"了。

**反例 2（2026-05 射雕会话踩坑）**：图方便把 `read.py continue` 和 `precompose --peek-offset 0` 串在**同一条 background 命令**里（`read.py ... && precompose ...`）。结果 read.py 先把 progress 从 p105 推到 p110，紧接着 precompose 算的"当前批"变成 p110-114——而用户此刻还没听 p105-109（agent 还得另外发那一批）。等于跳过了一批，缓存彻底错位。

**铁律**：`read.py continue` 必须**前台同步**执行（agent 需要它的返回值来构造 MEDIA 文件名）；`precompose --peek-offset 0` 才放到 background。两者**不能 `&&` 串联**，因为串联后 precompose 算 offset 时 progress 已经被 read 推进过了。正确顺序是：

```
1. terminal (foreground): python3 read.py --mode continue --count 5
   → 拿到 paragraph_range [N, N+5)，progress 已被推进到 N+5
2. agent: 发 MEDIA:.../combined_chXXX_pN-p(N+4).wav
3. terminal (background=true): python3 precompose.py --peek-offset 0 --count 5
   → 此时 progress=N+5，预合成 p(N+5)-p(N+9)，正确
```

#### ⚠️ 状态错位时的恢复（progress 跑到了用户耳朵前面）

如果由于**任何原因**（手工补发上一批漏掉的音频、用户切章 locate、agent 误调用了 read.py 多推进了一次）导致**当前正在播放的批次 < progress 指针**，那么继续按 `--peek-offset 0` 启动预合成会**跳过用户的下一批**，下次"继续"必然现合成。

**症状**：用户说"继续"，agent 检查预期文件名 → 不存在 → 临时合成（5-10 秒等待）。

**诊断**：发完上一批 MEDIA 后看一眼最近的预合成日志里 `paragraph_range` 是不是和"用户接下来该听的范围"对得上。

**修复路径**（按场景选）：

1. **补发场景**（agent 自己把进度往前推过头了）：直接现合成那一批（`win_tts.sh` + 拼接文本），progress 不动；下一轮"继续"自然会和 progress 对齐，预合成链恢复。
2. **切章/locate 场景**：locate 之后**重新启动**预合成，且 offset 仍是 0（locate 会把 progress 设到目标位置，"下一批"就是 progress 当前位置）。
3. **未来防呆**：每次发完 MEDIA、起预合成前，agent 心里默念一遍——"我刚刚发的 wav 文件名里的段号区间，是不是 = read.py 上次返回的 paragraph_range？" 若不是，说明状态错位，先修复对齐再起预合成。

**铁律补强**：`read.py continue` → 发 MEDIA → `precompose --peek-offset 0` 这三步是**原子的**，中间**不要**插入任何额外的 read.py 调用或 locate 调用。任何打断顺序的操作（包括"我先看一眼下一段是什么"）都会让 progress 偏离用户耳朵的位置。

#### ⚠️ 用户连续"继续"时的时序竞争（2026-05 实战教训）

正常节奏（预合成跑得过用户）：

```
T0  progress=p100  用户: 继续
T1  read.py → 推进到 p105，发 p100-104 wav
T2  后台 precompose 启动，目标 p105-109
T3  预合成 ~60s 完成 p105-109.wav  ← 用户在此之前说"继续"会出问题
T4  用户: 继续 → 命中 p105-109 缓存 ✅
```

竞争场景（用户在预合成完成前就追"继续"）：

```
T0  progress=p100  用户: 继续
T1  read.py → 推进到 p105，发 p100-104 wav
T2  后台 precompose 启动，目标 p105-109（还在跑）
T3  用户: 继续  ← 来早了！
T4  agent 找 p105-109 缓存 → 不存在
T5  agent 现合成 p105-109 → 还顺手又 read.py 推进到 p110，启动 precompose 目标 p110-114
T6  ⚠️ p105-109 的那次旧预合成此时跑完了——但它的目标是 progress=p105 时的"下一批"= p105-109，
     现在已经被现合成覆盖，浪费了一次 TTS
T7  用户: 继续 → 找 p110-114 缓存
T8  如果 T5 启动的 precompose 还没跑完，又是缓存未命中 → 再次现合成 → 再次 read.py 推进到 p115
T9  ⚠️ 此时旧的 precompose 已跑完 p115-119（基于当时 progress=p110 → offset=0 → p110-114）
     但 read.py 已经推进过 p115，下次"继续"需要的是 p120-124，p110-114 浪费
```

**问题本质**：read.py 推进进度时不知道"上一次后台预合成的目标是什么"，多次现合成 + 多次 precompose 会让目标错位。

**正确处理**（用户连续"继续"且预合成可能未完成时）：

1. **首选：检查并等待上一次后台预合成进程**。如果 `process(action="poll", session_id=<上次的>)` 显示 still running 且 uptime < 90s，先 wait 它，命中缓存比现合成快。
2. **次选：现合成 + 跳过本轮 precompose**。如果决定不等，直接现合成 p105-109，**不要再调 read.py continue 推进 progress**——progress 已经是 p105 不动，现合成填的就是 p105-109 这一批。然后才发 MEDIA。
3. **发完 MEDIA 后才**：调一次 `read.py --mode locate --chapter X --paragraph 110` 把 progress 推进到 p110（已发完的下一段），再启动 precompose 目标 p110-114。

**关键不变式**：每次发出一个 MEDIA wav 之前，progress.json 的 `current_paragraph` 必须等于"该 wav 末段 + 1"。read.py 的 continue 模式会自动满足，但**现合成路径必须手动 locate** 来对齐，否则就出现本会话的错位。

**反例（本会话 2026-05 当场犯）**：发完 p100-104 后用户立刻"继续"。我先调 read.py continue（progress p105→p110），然后发现 p105-109 没缓存，转去现合成 p110-114（因为 read.py 已经推到 p110 了），实际用户想听的是 p105-109，导致跳读。补救：用 locate 模式 + 手动构造文本现合成。

**侦测信号**：如果发现"刚发的 wav 文件名末段 + 1 ≠ progress 当前值"，说明 read.py 推过头了，必须现合成回补、用 locate 修正 progress。

#### 命中缓存

下次用户说"继续"时：

1. 调 `read.py --mode continue --count 5`（**正常更新进度**）拿到段落范围
2. 算出预期文件名：`combined_ch<NNN>_p<MMM>-p<KKK>.wav`
3. **检查文件存在且 size > 10KB** → 直接发 MEDIA
4. 不存在 → 现合成（兜底，等同于无预合成的情况）
5. **发完后再次启动后台预合成下一批**（链式继续）

#### precompose 输出 status 含义

| status | 含义 | 处理 |
|--------|------|------|
| `ok` | 新合成成功 | 后台任务正常结束 |
| `cached` | 已存在缓存 | 后台任务立即返回，无开销 |
| `skipped` (`book_end`) | 已到全书末尾 | 停止预合成 |
| `error` | TTS 失败 / 超字符上限 | 不报错给用户，下次继续时现合成 |

#### 边界

- **跨章节**：peek 模式自动处理（offset 累计走过章节末尾时跳到下一章）
- **磁盘**：每批 ~15MB，最多领先 1 批 = 30MB 上限，可控
- **失败容错**：后台合成失败不影响当前会话，下次现合成兜底

### 🔥 跨章批次处理铁律（2026-05 实战补丁）

**问题**：预合成 peek 算出的批次范围（如 `p205-p209`，5 段）可能**和真正 `continue` 取的范围不同**（如真实拿到 `p205-p210`，6 段，因 read.py 会一直取到 `end_idx = min(start+count, len(paragraphs))`）。文件名按 peek 命名时**少最后一段**，发 MEDIA 时用户会少听 1 段。

更糟糕的反例（射雕第二回末"金庸"署名噪音）：
- 真实 ch2 共 211 段（p0-p210），最后 p210 是孤立"金庸"两字
- `continue --count 5` 起点 p205 时：end_idx=min(210,211)=210，取 p205-p209（5段），next=ch2 p210
- 但**下一次** `continue --count 5` 起点 p210 时：end_idx=min(215,211)=211，取 p210 这 1 段，next=ch3 p0
- 这一段就是"金庸"，被独自合成 + 念给用户 = 突兀的孤立两字噪音

#### 正确做法（三条铁律，命中即用）

**铁律 1：发 MEDIA 前，先用 read.py 实际返回的 `paragraph_range` 构造文件名，不要用预合成 peek 时的名字。**

- continue 完拿到 `paragraph_range: [start, end_exclusive]`
- 文件名 = `combined_ch{NNN:03d}_p{start:03d}-p{end_exclusive-1:03d}.wav`
- 如果该文件**不存在**（说明 peek 算出的范围和真实不同），现合成兜底，不要发错文件名
- 文件名不一致是高频 bug，**不要相信预合成留下的文件名**

**铁律 2：是否跨章看 `is_chapter_end` 字段，不要靠 `next_paragraph` 推断。**

- `is_chapter_end == true` → 本批是当前章最后一批，下次"继续"会进入新章
- 跨章前后预合成可能失效（peek 不一定算对新章首批），下次"继续"时检查文件存在 → 不存在就现合成

**铁律 3：章末单字/短段（< 10 字）= 噪音残留，跳过不念。**

- 已知三联版每章末有孤立"金庸"两字
- read.py 取到的 `selected[-1].text.strip()` 如果长度 < 10 字且是常见署名词（金庸/作者名/版权号），**从拼接文本中删除该段，但 progress 正常推进**
- 实现位置：agent 层拼接时过滤，**不要**改 read.py（read.py 是通用的，过滤是版本特定噪音）
- 过滤后如果拼接文本为空（全是噪音），不要合成，直接跳过这批，再调一次 continue

#### 实战代码模板

```python
import json, subprocess
r = subprocess.run(['python3', '.../read.py', '--book', BOOK, '--mode', 'continue', '--count', '5'],
                   capture_output=True, text=True)
data = json.loads(r.stdout)
p_start, p_end = data['paragraph_range']  # [start, end_exclusive]
chapter = data['chapter']

# 噪音过滤
NOISE_PATTERNS = {'金庸'}  # 三联版章末署名
paras = [p for p in data['paragraphs']
         if not (len(p['text'].strip()) < 10 and p['text'].strip() in NOISE_PATTERNS)]

if not paras:
    # 全是噪音，再走一次 continue（极少发生）
    ...
else:
    text = '\n\n'.join(p['text'] for p in paras)
    # 用真实最后一段的 index 命名文件
    last_idx = paras[-1]['index']
    first_idx = paras[0]['index']
    out_name = f'combined_ch{chapter:03d}_p{first_idx:03d}-p{last_idx:03d}.wav'
    # 检查缓存命中 → 否则现合成
```

#### 长期修复方向（未做，待用户决策）

- `read.py` 可加 `--skip-noise` 参数，把过滤内化进脚本，agent 层不用每次处理
- `precompose.py` 应跟着同步，保证预合成的文件名和 continue 真实范围一致
- 暂未实现，因为：(1) 噪音过滤是版本特定的（新修版可能不同），(2) read.py 通用性更重要

#### 缓存未命中的现合成兜底（`scripts/synth_batch.py`）

当 precompose 用错 offset / 还没跑完 / 失败，而用户已经说"继续"时，用兜底脚本**按指定段范围**直接合成：

```bash
source ~/hermes_data/ebooks/.venv/bin/activate && \
python3 ~/.hermes/skills/media/audiobook-reader/scripts/synth_batch.py \
  --book "<书名>" --chapter N --start P --count 5
```

⚠️ 内部用 `read.py --mode locate` 取段，会把 progress 写到 `[P, P+C)`。多数兜底场景下 progress 已经 ≥ P+C（read.py 已先推进过），调用 synth_batch 等于"回滚再前进"，最终落点不变；但若 progress < P 会造成跳跃，使用前自查。文件名按 `combined_ch{NNN}_p{P}-p{P+C-1}.wav` 闭区间规则写。

## 章节切分规则（txt 格式）

txt 没有结构化章节，按以下正则匹配章节标题（按顺序尝试）：
1. `^第[一二三四五六七八九十百千零〇\d]+[回章节卷篇]\s*.*$`（中文章节）
2. `^Chapter\s+\d+`（英文）
3. `^卷[一二三四五六七八九十\d]+\s*.*$`
4. 都不匹配 → 整本书作为单章

详细规则见 `references/segment_rules.md`。
书源站点、苦瓜书盘下载流程、金庸版本说明见 `references/book_sources.md`。

**找书渠道实测与版本辨识见 `references/free-book-sources.md`**（含 Anna's Archive / Z-Library 在当前环境不可达的实测、苦瓜书盘搜索陷阱、金庸三联版 vs 新修版区分）。

## 段落切分规则

1. 按原文自然段（`\n\n` 或单 `\n`）初切
2. 合并相邻短段（合并后 ≤ 500 字才合并）
3. 切分长段：按 `。！？` 切，单段 ≤ 500 字
4. 跳过纯空白段

## 进度文件结构

```json
{
  "current_chapter": 3,
  "current_paragraph": 12,
  "last_read_at": "2026-05-29T18:30:00",
  "total_paragraphs_read": 45
}
```

进度语义：`current_chapter/paragraph` 指向**下一段要读的位置**（已读过的段落不在此）。

## 常见问题与陷阱

### 0. 下载的文件必须有正确扩展名
`add_book.py` 按 `--source` 的扩展名分发 parser。如果用 `curl -o /tmp/file.bin` 下载然后导入，会报 `ValueError: 不支持的格式: .bin`。

**正确做法**：下载时就用正确扩展名（mobi/epub/txt），或导入前 `mv /tmp/file.bin /tmp/file.mobi`。

URL 下载时 `fetch_source()` 会尝试从 URL 推断扩展名，但很多下载站走的是 `?id=xxx` 形式的动态路径，推断会失败 → 退回 `epub` 默认值 → 后续解析炸。**推荐：本地先 curl 下来命名好，再用 `--source 本地路径` 导入**。

### 1. epub 章节 spine 顺序
ebooklib 的 `book.spine` 给的是 idref，需要用 `book.get_item_with_id()` 反查。直接遍历 `get_items_of_type(ITEM_DOCUMENT)` 顺序可能不对。

### 2. txt 编码
中文 txt 常见编码：utf-8 / gb18030 / gbk。用 `chardet` 探测，但 chardet 对短文本不准，至少读 100KB 再探测。

### 3. epub 里的 HTML 噪音
章节 HTML 里常混入 `<style>`、`<script>`、`<nav>`、版权页。提取正文前清洗这些标签。

### 4. 音频缓存命名
`ch<3位章号>_p<3位段号>.wav`，例如 `ch001_p005.wav`。这样同书多个段不冲突。

### 5. 并行进度
每本书自己一个 progress.json，互不干扰。Agent 只需根据 `--book` 参数路由即可。

#### 5.1 书名带版本后缀时的续读解析

用户口语里常只说基础书名（如「继续念射雕英雄传」），但书库里的真实目录可能带版本后缀（如「射雕英雄传（三联修订版）」/「射雕英雄传（新修版）」）。

标准处理：
1. 先按用户给出的书名调 `read.py`。
2. 若返回 `书不存在: <书名>`，不要立刻问用户；先调 `library.py list` 查书库。
3. 若只有一个候选匹配基础书名，直接用该候选。
4. 若多个候选匹配，优先选择**当前续读进度最靠后的版本**（通常就是用户正在听的版本）；若进度无法判断或用户明确指定版本，再询问。
5. 后续本轮都使用解析出的完整书名，避免反复 `书不存在`。

这样既尊重多版本并行进度，又避免用户每次必须说完整版本名。

### 6. 章节切分失败
若 txt 切出来只有 1 章但实际是多章节书，检查正则是否匹配到标题。常见原因：标题前有空格/全角空格。

### 7. 爬在线阅读站必须用后台进程
40 回左右的书爬一遍要 1-2 分钟（每页 1.2s 延迟 + 网络），**必然超过 `terminal()` 的 300s 前台超时**。前台跑会被中途杀掉，临时文件因为是一次性写出会全部丢失。

**正确**：`terminal(background=true, notify_on_complete=true)`，等通知后再处理。
**禁止**：`nohup ... &` / `disown` — Hermes 会拒绝执行（"Foreground command uses shell-level background wrappers"）。

详细的爬取流程、反爬识别、HTML 噪音清洗模板见 `references/scraping_book_sites.md`。

### 8. 反爬识别 — 见到 302 跳验证页立即换站
某些在线书站（如 jinyongx.com）会用 `HTTP 302 → /GE/CC/VALIDATOR?key=...&url=...` 这种 token 验证防爬。不要硬刚，列出 Bing 搜索的其他候选站（通常同书有 3+ 个源），找没反爬的那个。详见 `references/scraping_book_sites.md` 第 1 节。

## 不要做的事

- ❌ 不要在 read.py 里直接调 TTS（违反分层）
- ❌ 不要把音频文件存到 `/tmp`（重启丢失，且没法复用）
- ❌ 不要忘记更新 progress.json
- ❌ 不要假设 epub 章节顺序等于文件顺序
- ❌ 不要用 cat/echo 写大段文本，用 write_file 工具
- ❌ **不要在同一条回复里把 MEDIA 音频和任何文字（章节标题/进度/剧情提示/emoji/标点装饰）混在一起**。混合发送会让 QQ Bot 丢弃 MEDIA 附件，用户只看到文字、收不到音频。详细规则与正反例见上文「⚠️ QQ Bot 听书交付的铁律」章节。

## 依赖

```bash
# 在 ~/hermes_data/ebooks/.venv 这个独立 venv 里安装
pip install ebooklib beautifulsoup4 chardet lxml mobi
# pdf 支持（按需）：pip install pymupdf
```

依赖装在 `~/hermes_data/ebooks/.venv`，避免污染系统 Python。

**mobi 解析说明**：用 `mobi` 库（不是 calibre）。它会把 mobi 解包到临时目录，里面通常含 epub，再递归走 epub_parser。实测金庸 mobi（kgbook 来源）解出 41 章正常。
