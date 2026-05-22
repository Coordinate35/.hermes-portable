---
name: voice-message-delivery
description: 【语音消息·必加载】用户有自建 TTS 降级链（Windows GPT-SoVITS → MeloTTS → edge）。涉及"念/读/播报/语音说/朗读/口播"等请求，或 QQ Bot 回复，或任何要调用 text_to_speech 工具的场景，或抓取到微博推送场景，必须先加载本 skill，禁止直接调 text_to_speech 跳过本地服务。
author: coordinate35
category: media
---

# 语音消息投送管理

当需要以语音形式向用户发送消息时，按本 skill 的降级链和平台规则执行。

## 触发条件（命中任意一条立即加载本 skill）

- 用户说："语音说..." / "播报..." / "念一下..." / "读一下..." / "朗读..." / "口播..."
- QQ Bot 来源且短句（见下文"平台规则"）
- 需要将文本内容转换为语音文件发送
- 任何包含 `text_to_speech` 工具调用意图的场景

**自检问题**：「我接下来会不会调用 text_to_speech？」
- 是 → 必须先加载本 skill，再走 Windows → MeloTTS → edge 降级链
- 否 → 忽略

## ⚠️ 强制规则（曾被违反）

**任何时候要生成语音，禁止直接调用 `text_to_speech` 工具。**

- `text_to_speech` 工具默认走 edge，等于跳过优先级 1 和 2，违反用户既定 TTS 降级策略。
- 即使是即时短句回复，也必须按 Windows → MeloTTS → edge 顺序逐级尝试。

### curl 写入空文件的坑

`curl ... -o /some/dir/file.wav`，若目录不存在，curl 仍返回 HTTP:200 但 size=0。
**必须先 `mkdir -p` 输出目录，再 curl**，否则 WAV 是空文件，发出去 QQ 会拒收或静音。

## TTS 源优先级（从高到低）

| 优先级 | 名称 | 端点 | 调用方式 | 状态 |
|:---:|:---|:---|:---|:---:|
| 1 | Windows 宿主机 TTS | `http://192.168.56.1:9880` | POST JSON `→` WAV | 主力 |
| 2 | Linux 本地 MeloTTS | `~/hermes_data/melotts/melo_tts.py` | CLI `→` WAV | 备用 |
| 3 | Edge 在线 TTS | 微软服务器 | `text_to_speech` 工具 | 最终降级 |

### 1. Windows 宿主机本地服务（GPT-SoVITS V2）

```bash
curl -X POST "http://192.168.56.1:9880" \
  -H "Content-Type: application/json" \
  -d '{"text":"播报内容","text_language":"zh"}' \
  --output /tmp/output.wav \
  --connect-timeout 10
```

这是 **VirtualBox Host-Only 网络**。宿主机 IP 确认方法见下文「网络环境检查」。

**Shell 转义坑**：用 `$(cat file)` 传递含中文标点的文本时，bash 会解析特殊字符。
建议在 Python 脚本中用 `json.dumps()` 构造请求体。

### 2. Linux 本地 MeloTTS

```bash
cd ~/hermes_data/melotts
source .venv/bin/activate
python3 melo_tts.py "播报内容" /tmp/output.wav
```

**离线运行必须注意时序**：`HF_ENDPOINT` 和 `TRANSFORMERS_OFFLINE` 必须在 `import transformers` 或 `from melo.api import TTS` 之前设置。

```python
# ✔️ 正确：在 import 之前
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from melo.api import TTS  # import 之后不再设置上述环境变量
```

**误区**：在 `main()` 内设置环境变量，但 `from melo.api import TTS` 在文件顶部，导致 `transformers` 在 import 时就尝试连接 huggingface.co 而失败。

### 3. Edge 在线 TTS（最终降级）

使用 Hermes 内置 `text_to_speech` 工具，provider: `edge`。
当本地两个服务都不可用时自动降级到此。

## 平台感知消息规则（QQ Bot）

来源为 QQ Bot 时：

| 内容类型 | 处理方式 |
|:---|:---|
| 短句（一句话，无列表/代码/多层次信息） | **直接发语音消息** |
| 长文或复杂内容 | 先文字汇总，再语音播报摘要 |

判断标准：
- 短句 = 500 字以内，无需要列表、表格、代码块等格式化结构
- 复杂 = 500 自以上，含有多个独立信息点，需要结构化展示

## 网络环境检查

### VirtualBox Host-Only 网络 IP

当 Windows 宿主机作为 TTS 服务器，Linux 客户机访问时：

```bash
# Linux 客户机中查看 Windows 宿主机 IP
ip route | grep default
# 或
route -n
```

Host-Only 网卡默认通常为 `192.168.56.1`。若非此 IP，确认 VirtualBox 网络设置：
- 虚拟机 → 设置 → 网络 → 网卡 1: Host-Only Adapter
- 宿主机管理器 → 文件 → 首选项 → 网络 → 编辑 Host-Only 网络

### 验证 TTS 服务可用性

```bash
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
  "http://192.168.56.1:9880" || echo "TTS 服务不可达"
```

## 不要做的事

- ❌ 不要用 `$(cat file)` 向 curl JSON body 传递含中文标点的文本
- ❌ 不要在 import 之后设置 `HF_ENDPOINT`（对 transformers 无效）
- ❌ 不要用全文直接发语音（超长文本可能被截断或质量下降）
- ❌ 不要在复杂内容场景下忽略文字汇总
- ❌ 不要混淆 TTS 后端：默认 `text_to_speech` 走在线 edge，不等同于本地服务，两者不能混用

## 长文本分段处理

TTS 服务通常对单次输入长度有限制（GPT-SoVITS、MeloTTS、edge 各有阈值）。超过限制时按以下流程：

1. **切分**：按 `。！？\n` 优先切，回退到 `，；`，每段 ≤ 500 字符
2. **逐段合成**：每段调用 TTS，输出到 `/tmp/tts_seg_001.wav`, `/tmp/tts_seg_002.wav`...
3. **拼接**：用 ffmpeg concat demuxer 合并为单个文件

```bash
# 生成 concat 列表文件
for f in /tmp/tts_seg_*.wav; do echo "file '$f'"; done > /tmp/concat.txt

# 拼接（同采样率/编码时用 copy，否则去掉 -acodec copy 让 ffmpeg 重编码）
ffmpeg -y -f concat -safe 0 -i /tmp/concat.txt -acodec copy /tmp/final.wav
```

**采样率不一致的坑**：Windows GPT-SoVITS 输出可能是 32kHz，MeloTTS 是 44.1kHz，混用后 `-acodec copy` 会出错。降级链中只要切换过 TTS 源，就别用 copy，让 ffmpeg 重编码。

## 与其他技能的集成

### 与新闻类技能（如 wallstreetcn-news、weibo-monitoring）配合

新闻 → 语音播报标准流程：

1. 新闻技能拉取头条文本
2. 在 agent 层（cronjob prompt）做播报文案改写：加序号、加停顿（`，` `。`）、口语化
3. 调用本 skill 的三级降级链合成音频
4. 按平台规则交付：QQ 直接发语音；其他平台先文字摘要再补语音

**架构分层原则**：监控/采集脚本只产出文字（单一职责），TTS 合成和降级策略在 agent 层处理，保持脚本可复用、降级灵活。

## 音频文件清理

TTS 合成会在以下位置留下音频文件，长期累积会占用磁盘空间：

- `/tmp/*.wav` / `/tmp/*.mp3` — Windows/MeloTTS 合成产物
- `~/.hermes/audio_cache/*.mp3` — Edge TTS 缓存

**建议**：设置定时清理，保留最近 7 天的音频即可。已验证的清理脚本：

```bash
#!/bin/bash
# TTS 音频清理：删除 7 天前的临时音频
find /tmp -maxdepth 1 -type f \( -name "*.wav" -o -name "*.mp3" \) -mtime +7 -delete
find ~/.hermes/audio_cache -maxdepth 1 -type f -name "*.mp3" -mtime +7 -delete
```

搭配 cronjob 每天凌晨执行（参考 cronjob 工具）：
- schedule: `0 3 * * *`
- no_agent: true（纯脚本执行，无需 LLM 介入）

> 用户偏好：不需要统一规范化音频存放目录，直接按现有分散路径定时清理即可。
