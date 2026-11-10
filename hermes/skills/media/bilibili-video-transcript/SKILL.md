---
name: bilibili-video-transcript
description: Use when 要 B站视频逐字稿或要点总结。
author: coordinate35
category: media
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [bilibili, transcription, asr, whisper, video]
    related_skills: [article-archive, voice-message-delivery]
---

# B站视频转文字与要点整理

## When to Use
- “B站有很多视频，找一个靠谱的总结成文字”
- “这个视频讲了什么 / 转成文字 / 逐字稿”
- 需要补全某篇付费文章的正文（有人把原文朗读上传）

## 环境（已就绪，勿重复安装）
- venv：`~/hermes_data/asr-venv`（yt-dlp + faster-whisper 1.2.1）
- 模型缓存：`~/hermes_data/asr-models`（small）
- 中间产物：`/tmp/bili_audio`、`/tmp/bili_asr`
- ffmpeg：`~/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffmpeg`

**装包必须走镜像**：`--index-url https://pypi.tuna.tsinghua.edu.cn/simple`。直连 PyPI 实测约 1MB/min（40MB 的 ctranslate2 要几十分钟），清华源 12 秒装完。模型下载设 `HF_ENDPOINT=https://hf-mirror.com`（实测 0.8s 响应）。

## 第 1 步：搜片（无需登录）
```
https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=<urlencode>&page=1&order=pubdate
```
带桌面 Chrome 的 `User-Agent` + `Referer: https://www.bilibili.com/`。

- 连续快速请求会 `HTTP 412`：每次之间 sleep 0.6s，不要并发。
- 不要用 `--get --data-urlencode` 拼参数：会拿到风控 HTML（不是 JSON），解析直接炸。

## 第 2 步：判断“靠谱”
优先级：官方/机构号 > 照读原文 > 二次解读；播放量只作参考。
缺一不可的判据：
1. 发布时间与事件时间吻合；
2. 若声称照读原文，逐段对得上已知文本；
3. **两条独立视频的关键数字完全一致** → 才敢认定是忠实朗读，而非 UP 主自算；
4. 抽查 1–2 个可外部核实的硬事实（法案票数、监管数据等）；
5. 无荐股、喊单、带货。

## 第 3 步：取音轨
```bash
~/hermes_data/asr-venv/bin/yt-dlp -f "bestaudio/best" -x --audio-format m4a \
  -o "/tmp/bili_audio/%(id)s.%(ext)s" --no-playlist "https://www.bilibili.com/video/<BV>"
```
8–9MB / 17 分钟，实测约 5MB/s。

## 第 4 步：转写（最容易踩的坑）
**不要把 m4a 路径直接传给 `model.transcribe`**：faster-whisper 1.2.1 会调 `av.open(..., metadata_errors="ignore")`，而装到的 PyAV 19 不认该参数 → `TypeError: open() got an unexpected keyword argument 'metadata_errors'`。

绕法：ffmpeg 转 16k 单声道 wav → wave + numpy 读成 float32 数组 → 喂模型。

```python
subprocess.run([FFMPEG, "-y", "-i", m4a, "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", wav], capture_output=True)
with wave.open(wav, "rb") as w:
    raw = w.readframes(w.getnframes())
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
model = WhisperModel("small", device="cpu", compute_type="int8",
                     download_root="~/hermes_data/asr-models")
segs, info = model.transcribe(audio, language="zh", beam_size=5, vad_filter=True)
```

耗时：17 分钟音频约 8 分钟（CPU 260%）。放 `background=true, notify=true` 跑。

## 第 5 步：整理要点
- 每条要点带时间戳（`[05:39]`），用户可回看核对。
- **口径三段分离**：原文（公开转载）／朗读转写／UP 主个人观点，混在一起等于造谣。
- ASR 专名错得离谱但数字通常可靠：VIX→VIS/VRX、NeoCloud→MuCloud、CDS→Cities、滞胀→智障、洪灏→红号、人名（Abbott、Hinojosa）乱码。专名必须按上下文＋常识校订。
- 听不清的句子不要硬还原，标「存疑」，宁缺勿编。
- 若视频是朗读某篇付费文章：与公开转载版能对齐的部分按逐字引用，朗读独有的部分必须标“据朗读转写，非原文措辞”。

## 不可用的捷径（别再试）
- `/x/player/v2` 的字幕轨：未登录基本为 0 条（弹幕同样为 0）。
- `/x/web-interface/view/conclusion/get`（B站 AI 总结）：返回 `-403 访问权限不足`。

## 交付
- md + PDF 存 `~/hermes_data/articles/`；PDF 用 `build_article_pdf.py`。
- 该构建器只认 `**整行**` 作为小标题，不解析 `##`／`###` 和行内 `**`（会原样显示）；正文含 emoji 会 `PDF_FONT_FAIL`，先用文字标记替换。
- 构建命令带 `PYTHONPATH=` 前缀，用 `~/hermes_data/rl-venv/bin/python`。
