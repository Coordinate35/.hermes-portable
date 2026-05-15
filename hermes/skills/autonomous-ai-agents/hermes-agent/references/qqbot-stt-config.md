# QQ Bot STT 配置与架构

> Session: 2026-05-15 | Signal: QQ Bot 语音识别失败时，全局 `stt.local.model` 配置对 QQ Bot 完全无效。

## 核心事实

QQ Bot 的语音处理是 **两层传感架构**，与全局 `stt` 配置无关：

```
QQ 语音消息
    ↓
① 腾讯内置 ASR（QQ 服务器）
    ↓ 有结果？
    ├── ✅ 有 → 直接使用，流程结束
    └── ❌ 空/失败 → 继续
        ↓
② 外部 STT API（需配置 channels.qqbot.stt 或 QQ_STT_API_KEY）
    ↓ 有结果？
    ├── ✅ 有 → 用外部结果
    └── ❌ 未配置/失败 → [Voice] [语音识别失败]
```

## 配置路径（独立于全局 stt）

### 方式 A：配置文件（config.yaml）

```yaml
channels:
  qqbot:
    stt:
      enabled: true
      provider: "openai"      # 或 "zai" / "glm"
      baseUrl: "https://api.openai.com/v1"
      apiKey: "sk-..."
      model: "whisper-1"
```

### 方式 B：环境变量

```bash
export QQ_STT_API_KEY="sk-..."
export QQ_STT_BASE_URL="https://api.openai.com/v1"
export QQ_STT_MODEL="whisper-1"
```

### 方式 C：本地 HTTP API（推荐）

本地启动 faster-whisper 服务，QQ Bot 指向本地端口：

```yaml
channels:
  qqbot:
    stt:
      enabled: true
      baseUrl: "http://127.0.0.1:8000"
      apiKey: "any-key"
      model: "medium"
```

## 模型缓存路径

```
~/.cache/huggingface/hub/models--Systran--faster-whisper-medium/
    ├── snapshots/
    │   └── <revision>/
    │       ├── config.json
    │       ├── model.bin       ← ~1.5GB
    │       └── tokenizer.json
    └── 其他 HuggingFace hub 文件
```

## 国内下载镜像

默认从 HuggingFace Hub 下载，国内可能失败。使用镜像站：

```bash
HF_ENDPOINT=https://hf-mirror.com python -c "
from faster_whisper import WhisperModel
model = WhisperModel('medium', device='cpu', compute_type='int8')
"
```

## 日志验证

检查 gateway.log 确认 QQ Bot 走的是哪条路：

```bash
# 看到这个说明外部 STT fallback 未配置
grep "STT not configured\|Voice STT failed\|ASR returned empty" ~/.hermes/logs/gateway.log
```

## Pitfall: 全局 stt 配置对 QQ Bot 无效

错误认知：改了 `stt.local.model = medium` 就能提升 QQ 语音识别准确度。

事实：QQ Bot 完全不读取 `stt.*` 配置，只认 `channels.qqbot.stt.*` 或 `QQ_STT_*` 环境变量。

解决：如需优化 QQ 语音识别，必须单独配置 QQ Bot 的 STT fallback。

## Pitfall: MeloTTS 在中文数字/特殊字符上崩溃

MeloTTS 对包含数字和特殊标点的中文文本支持很差，会报 `AssertionError` （位于 `melo/text/chinese.py` line 122、`chinese_mix.py` line 228 等）。

触发情况：中文文本里出现阿拉伯数字（如 `2026`、`140.19`）、百分号（`5%`）、希腊字母（`GDP`、`M2`）、或者某些标点符号。

解决：含有数字/标点的长文本，应该使用 **Edge TTS**（Hermes 内置默认）而非 MeloTTS。MeloTTS 适合纯中文短句，不含数字和特殊字符。
