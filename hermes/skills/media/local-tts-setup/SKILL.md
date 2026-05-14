---
name: local-tts-setup
description: 在无 GPU 或 GPU 不可用的 Linux 环境中快速部署本地轻量级 TTS。主要采用 Piper（ONNX 时间模型，纯 CPU 实时推理），包含完整的环境诊断、依赖解决、模型下载（国内镜像）、故障排查。适用于虚拟机、无独显存储服务器、边缘设备等场景。
title: 本地轻量 TTS 部署（Piper 纯 CPU 模式）
trigger: |
  需要本地 TTS 合成但没有 GPU 或 GPU 不可用；
  edge-tts / 云 TTS 失败或不可用；
  VirtualBox / WSL / 容器等虚拟化环境需要语音合成；
  需要离线 TTS 不想依赖外部 API；
  Piper 安装、下载模型、运行测试。
---

# 本地轻量 TTS 部署指南

## 快速决策树

```
是否需要极致自然度 / 情感表达 / 声音克隆？
┌───────────────────────────────────────────┐
│  是 → ChatTTS / Sherpa-ONNX                   │
│  需要 6GB+ GPU 显存                        │
│  虚拟机不可用 → 参考 virtualbox-gpu-bridge   │
└───────────────────────────────────────────┘
            │ 否
            ▼
    是否只需要基本播报/通知/简单语音？
    ┌────────────────────────────┐
    │  是 → Piper （本 Skill 内容）            │
    │  纯 CPU、实时、离线、轻量              │
    └─────────────────────────────────┘
            │ 否
            ▼
    最简单机械音 → espeak-ng
```

## 方案对比

| 特性 | **Piper** | ChatTTS | espeak-ng |
|:---|:---|:---|:---|
| 自然度 | 星星星 清晰但偏机械 | 星星星星星 接近真人 | 星 机械感强 |
| GPU 需求 | 不需要 | 6GB+ | 不需要 |
| 推理速度 | CPU 实时 | GPU 1-3秒 | CPU 实时 |
| 模型大小 | 30-100 MB | 3-4 GB | 内置 |
| 情感/笑声 | 不支持 | 支持 | 不支持 |
| 离线 | 是 | 是 | 是 |
| 英中混合 | 支持 | 支持 | 支持 |

## Step 1: 环境诊断

执行以下检查，确认最佳安装方式：

```bash
# 1. GPU 检查（如果返回 False，跳过 GPU 方案）
python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "PyTorch 未安装"

# 2. Python 环境
which python3 && python3 --version
which pip || which uv || echo "既无 pip 也无 uv"

# 3. 网络访问（测试 HuggingFace 可达性）
curl -sI https://huggingface.co | head -1 || echo "HuggingFace 不可达"

# 4. sudo 权限
check
sudo -n true 2>/dev/null && echo "有 sudo" || echo "无 sudo 或需要密码"
```

**根据诊断结果选择方案：**

| 检查项 | 结果 | 对应操作 |
|:---|:---|:---|
| `pip` 存在 | 是 | 直接 `pip install piper-tts` |
| `pip` 不存在，`uv` 存在 | 是 | `uv venv + uv pip install` |
| 都不存在 | 是 | 先安装 pip 或 uv |
| 系统 Python 被外部管理 | 是 | 必须用虚拟环境（venv） |
| HuggingFace 不可达 | 是 | 使用 hf-mirror.com |
| espeak-ng 二进制不存在 | 是 | Piper Python 包通常自带 phonemize，可继续；若报错再装 |

## Step 2: 安装 Piper

### 方式 A：pip 可用

```bash
pip install piper-tts
```

### 方式 B：uv 可用（推荐，更快更可靠）

```bash
# 创建独立虚拟环境
mkdir -p ~/hermes_data/piper
cd ~/hermes_data/piper
uv venv
source .venv/bin/activate

# 安装 Piper
uv pip install piper-tts
```

### 方式 C：系统 Python 被外部管理

如果执行 `pip install` 时报错 "externally managed"，必须用虚拟环境：

```bash
python3 -m venv ~/hermes_data/piper/.venv
source ~/hermes_data/piper/.venv/bin/activate
pip install piper-tts
```

## Step 3: 下载中文模型

### 模型目录结构

```
~/hermes_data/piper/
├── .venv/           # Python 虚拟环境
├── models/
│   ├── zh_CN-huayan-medium.onnx        # 模型文件
│   └── zh_CN-huayan-medium.onnx.json   # 配置文件
├── g2pW/            # chaowen/xiao_ya 模型需要的音素模型
│   ├── g2pw.onnx
│   └── ...
└── tts.sh           # 便捷脚本
```

### 中文模型可用清单

Piper 中文只有 **3 个女声**说话人，**无男声模型**，无 high 版本：

| 说话人 | 模型 | 大小 | 依赖 | 特点 |
|:---|:---|:---:|:---|:---|
| **华言** | `zh_CN-huayan-medium` | ~60MB | 无额外依赖 | 标准女声，**开箱即用**（推荐） |
| | `zh_CN-huayan-x_low` | ~30MB | 无额外依赖 | 快速，质量稍降 |
| **超文** | `zh_CN-chaowen-medium` | ~60MB | **需要 g2pw + torch** | 偏成熟女声 |
| **小雅** | `zh_CN-xiao_ya-medium` | ~60MB | **需要 g2pw + torch** | 偏年轻女声 |

> ⚠️ 注意：`zh_CN-huayan-high` **不存在**，high 路径会 404。

### 下载命令

```bash
cd ~/hermes_data/piper
mkdir -p models
cd models

# 主源（HuggingFace）
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json

# 国内镜像（当 HuggingFace 不可达时使用）
wget https://hf-mirror.com/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
wget https://hf-mirror.com/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
```

## Step 4: 测试合成

```bash
cd ~/hermes_data/piper
source .venv/bin/activate

echo "你好，这是 Piper 语音合成测试。" | piper \
  --model models/zh_CN-huayan-medium.onnx \
  --output_file test.wav

# 验证文件
ls -lh test.wav
file test.wav   # 应显示: RIFF WAVE audio, PCM, 16 bit, mono 22050 Hz
```

## Step 4.5: 非 huayan 模型的额外依赖（chaowen / xiao_ya）

⚠️ **如果使用 `zh_CN-chaowen-medium` 或 `zh_CN-xiao_ya-medium`，需要额外配置，huayan 不需要。**

### 安装额外 Python 依赖

```bash
cd ~/hermes_data/piper
source .venv/bin/activate

# 使用 uv
uv pip install g2pw torch --index-url https://download.pytorch.org/whl/cpu
uv pip install requests unicode-rbnf sentence-stream

# 或使用 pip
pip install g2pw torch --index-url https://download.pytorch.org/whl/cpu
pip install requests unicode-rbnf sentence-stream
```

### 下载 g2pw 音素模型

`chaowen` / `xiao_ya` 需要 g2pW 音素转换模型，Piper 会自动尝试从 HuggingFace 下载，但虚拟机/国内环境通常不可达。需要手动下载：

```bash
cd ~/hermes_data/piper
mkdir -p g2pW
cd g2pW

# 从国内镜像下载
wget --timeout=60 https://hf-mirror.com/datasets/rhasspy/piper-checkpoints/resolve/main/zh/zh_CN/_resources/g2pw.tar.gz

# 解压
tar -xzf g2pw.tar.gz
rm g2pw.tar.gz

# 确认结构
ls -lh
# 应包含: g2pw.onnx, config.py, MONOPHONIC_CHARS.txt, POLYPHONIC_CHARS.txt, version
```

### 设置 HuggingFace 镜像（下载 BERT tokenizer 用）

`g2pw` 会调用 `transformers` 库加载 `bert-base-chinese` tokenizer。如果环境不能访问 HuggingFace 原站，需要设置镜像端点：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

**建议永久化到 shell 配置：**

```bash
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.bashrc
source ~/.bashrc
```

### 测试 chaowen / xiao_ya

```bash
cd ~/hermes_data/piper
source .venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com

# 超文
echo "你好，这是超文的语音测试。" | piper \
  --model models/zh_CN-chaowen-medium.onnx \
  --output_file test_chaowen.wav

# 小雅
echo "你好，这是小雅的语音测试。" | piper \
  --model models/zh_CN-xiao_ya-medium.onnx \
  --output_file test_xiao_ya.wav
```

## Step 5: 便捷脚本

创建 `~/hermes_data/piper/tts.sh`：

```bash
#!/bin/bash
set -e

TEXT="${1:-你好，这是一段语音测试。}"
OUTPUT="${2:-output.wav}"
MODEL="${MODEL:-$(dirname "$0")/models/zh_CN-huayan-medium.onnx}"

source "$(dirname "$0")/.venv/bin/activate"

echo "[合成] $TEXT"
echo "       → $OUTPUT"

echo "$TEXT" | piper \
    --model "$MODEL" \
    --output_file "$OUTPUT" \
    --sentence-silence 0.2

echo "[完成] 音频已保存: $OUTPUT"
```

赋予执行权限：
```bash
chmod +x ~/hermes_data/piper/tts.sh
```

使用：
```bash
./tts.sh "你好，世界" output.wav
```

## 常见问题与排查

### Q1: `云 TTS` 失败了，还有别的选择吗？
- edge-tts 等云服务可能因网络或 API 限制失败
- 本地 Piper 是最可靠的 fallback，纯离线运行

### Q2: 提示 `espeak-ng not found`
- Piper Python 包通常自带 phonemize 工具，无需系统 espeak-ng 二进制
- 若确实报错，尝试安装：`apt-get install espeak-ng` 或 `brew install espeak`
- 检查：`dpkg -l | grep espeak` 确认库是否已安装

### Q3: `pip: command not found`
- 检查：`which pip` / `which pip3`
- 无 pip 时，检查 `uv`：`which uv` 或 `ls ~/.local/bin/uv`
- 使用 uv 替代：`uv venv && source .venv/bin/activate && uv pip install piper-tts`

### Q4: 系统 Python 被外部管理（externally managed）
- 这是 Debian/Ubuntu 22.04+ 的安全机制
- **必须** 使用虚拟环境，禁止用 `--break-system-packages`
- 正确做法：`python3 -m venv ~/.venv/piper && source ~/.venv/piper/bin/activate && pip install piper-tts`

### Q5: HuggingFace 下载超时/失败 / `Network is unreachable`

- 切换到国内镜像：将 URL 中的 `huggingface.co` 替换为 `hf-mirror.com`
- 示例：`https://hf-mirror.com/rhasspy/piper-voices/...`
- **对于虚拟机 / 国内服务器**，HuggingFace 原站通常完全不可达，**必须**使用镜像

### Q6: 使用 chaowen / xiao_ya 时报错 `No module named 'g2pw'`

这些模型需要额外的中文音素转换依赖：

```bash
uv pip install g2pw torch --index-url https://download.pytorch.org/whl/cpu
uv pip install requests unicode-rbnf sentence-stream
```

### Q7: 使用 chaowen / xiao_ya 时报错 `Downloading g2pW model... Network is unreachable`

Piper 尝试自动下载 g2pw 模型失败。需要手动下载并解压到正确位置：

```bash
cd ~/hermes_data/piper/g2pW
wget https://hf-mirror.com/datasets/rhasspy/piper-checkpoints/resolve/main/zh/zh_CN/_resources/g2pw.tar.gz
tar -xzf g2pw.tar.gz
rm g2pw.tar.gz
```

### Q8: 使用 chaowen / xiao_ya 时报错 `Cannot send a request, as the client has been closed`

`g2pw` 的 `transformers` 库尝试从 HuggingFace 下载 `bert-base-chinese` tokenizer。设置镜像端点：

```bash
export HF_ENDPOINT=https://hf-mirror.com
# 永久化：echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.bashrc
```

### Q9: 模型下载速度慢
- 中文 medium 模型约 60MB
- 使用 `--show-progress` 查看下载进度
- 或先下载到本地再上传到服务器

### Q10: 音频没有声音 / 声音不正常
- 检查模型是否完整：`.onnx` 和 `.onnx.json` 必须成对存在
- 检查音频格式：`file output.wav` 应显示 WAV 格式
- 试用不同音频播放器播放
- 尝试切换到 `huayan` 模型（无额外依赖，最稳定）

## 高级用法

### 切换音色
Piper 音色由模型文件决定，换模型 = 换音色。下载其他模型后，通过环境变量指定：

```bash
MODEL=/path/to/other_model.onnx ./tts.sh "文本"
```

### 调整语速
Piper 本身不支持直接调速，需要用 `sox` 等工具后处理：

```bash
sox input.wav output.wav tempo 1.2   # 加快 20%
sox input.wav output.wav tempo 0.8   # 放慢 20%
```

### 批量合成

```bash
# 逐行读取文本文件合成
while IFS= read -r line; do
    echo "$line" | piper --model model.onnx --output_file "out_$(date +%s).wav"
done < input.txt
```

## 参考资源

- Piper GitHub: https://github.com/rhasspy/piper
- Piper 语音模型库: https://huggingface.co/rhasspy/piper-voices
- HuggingFace 国内镜像: https://hf-mirror.com
- ONNX Runtime 文档: https://onnxruntime.ai/
