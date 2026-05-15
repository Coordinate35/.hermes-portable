---
name: local-tts-setup
description: 在无 GPU 或 GPU 不可用的 Linux 环境中快速部署本地轻量级 TTS。主要采用 Piper（ONNX 时间模型，纯 CPU 实时推理），包含完整的环境诊断、依赖解决、模型下载（国内镜像）、故障排查。适用于虚拟机、无独显存储服务器、边缘设备等场景。
title: 本地轻量 TTS 部署（Piper / MeloTTS 纯 CPU 模式）
trigger: |
  需要本地 TTS 合成但没有 GPU 或 GPU 不可用；
  edge-tts / 云 TTS 失败或不可用；
  VirtualBox / WSL / 容器等虚拟化环境需要语音合成；
  需要离线 TTS 不想依赖外部 API；
  Piper 安装、下载模型、运行测试；
  MeloTTS 安装、下载模型、运行测试。
---

# 本地轻量 TTS 部署指南

## 快速决策树

```
是否需要极致自然度 / 情感表达 / 声音克隆？
┌──────────────────────────────────────────────────────────────┐
│  是 → ChatTTS / Sherpa-ONNX                   │
│  需要 6GB+ GPU 显存                        │
│  虚拟机不可用 → 参考 virtualbox-gpu-bridge   │
└───────────────────────────────────────────────────────────────┘
            │ 否
            ▼
    是否需要中文且对韵律/断句有要求？
    ┌──────────────────────────────────────────┐
    │  是 → MeloTTS （本 Skill MeloTTS 部分）      │
    │  纯 CPU、离线、中文韵律明显优于 Piper     │
    └───────────────────────────────────────────────────────────┘
            │ 否
            ▼
    是否只需要基本播报/通知/简单语音？
    ┌────────────────────────┐
    │  是 → Piper （本 Skill Piper 部分）            │
    │  纯 CPU、实时、离线、轻量              │
    └────────────────────────────────────────┘
            │ 否
            ▼
    最简单机械音 → espeak-ng
```

## 方案对比

| 特性 | **Piper** | **MeloTTS** | ChatTTS | espeak-ng | Edge TTS |
|:---|:---|:---|:---|:---|:---|
| 自然度 | ⭐⭐ 清晰但偏机械 | ⭐⭐⭐⭐ 播音腔，韵律自然 | ⭐⭐⭐⭐⭐ 接近真人 | ⭐ 机械感强 | ⭐⭐⭐⭐ 较自然 |
| 中文断句/韵律 | ⭐ 机械硬切，无呼吸感 | ⭐⭐⭐⭐ 语义切分，停顿自然 | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| GPU 需求 | 不需要 | 不需要 | 6GB+ | 不需要 | 不需要 |
| 推理速度 | CPU 实时 | CPU ~1x实时（略慢） | GPU 1-3秒 | CPU 实时 | 网络 API 秒回 |
| 模型大小 | 30-100 MB | ~500MB+（含 BERT） | 3-4 GB | 内置 | 无（云端） |
| 离线 | 是 | 是 | 是 | 是 | **否** |
| 英中混合 | 支持 | 支持 | 支持 | 支持 | ⚠️ 语音需匹配语言 |
| 安装复杂度 | 极简 | 中等（需 PyTorch） | 复杂 | 极简 | 极简 |

> 💡 **选型建议**：
> - 中文、离线、对韵律有要求 → **MeloTTS** 
> - 中文、离线、只要能听懂就行 → **Piper**
> - 中文、有网、追求最佳效果 → **Edge TTS** (`zh-CN-XiaoxiaoNeural`)
> - 英文、离线 → **Piper** 或 **MeloTTS**

> ⚠️ **关键决策**：如果当前 TTS provider 是 Edge TTS 且配置的 voice 是英文（如 `en-US-AriaNeural`），**中文文本会直接失败或产生 1-2 秒的截断音频**。此时不要试图调试 Edge TTS，直接切换到 Piper。

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

> ✅ 实际验证：`piper-tts` PyPI 包在 VirtualBox / 无 GPU 环境下直接可用，不需要系统级别的 `espeak-ng` 二进制。它内置了音素化（phonemize）逻辑。

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

---

## Step 6: MeloTTS 部署（纯 CPU，中文韵律优于 Piper）

MeloTTS 是 MyShell AI 开源的轻量级 TTS，基于 VITS + BERT 韵律建模，中文语音的断句和停顿明显优于 Piper。纯 CPU 推理速度约 1x 实时（合成 80 秒音频约需 90 秒）。

### 安装 MeloTTS

```bash
mkdir -p ~/hermes_data/melotts && cd ~/hermes_data/melotts
uv venv
source .venv/bin/activate

# 必须从 GitHub 安装：PyPI 包缺少 requirements.txt，会构建失败
uv pip install git+https://github.com/myshell-ai/MeloTTS.git
```

> ⚠️ **Pitfall**: `uv/pip install melotts` 从 PyPI 安装会报错 `No such file or directory: requirements.txt`。必须使用 Git 源码安装。

### CPU 环境修复：torchaudio CUDA 依赖

MeloTTS 依赖会自动安装 CUDA 版本的 torchaudio，在无 GPU 环境下会报错：
```
OSError: libcudart.so.13: cannot open shared object file
```

需要强制重新安装 CPU 版本：
```bash
uv pip install torchaudio --index-url https://download.pytorch.org/whl/cpu --force-reinstall
```

### 设置 HuggingFace 镜像

MeloTTS 首次运行会下载 `bert-base-multilingual-uncased` tokenizer。国内/虚拟机环境必须设置镜像：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### MeCab 懒加载修复

MeloTTS 的 `melo/text/japanese.py` 在模块导入时就调用 `MeCab.Tagger()`，若 unidic 词典未就绪会抛出 `RuntimeError`，导致整个包无法导入。

**快速修复**（无需等待 unidic 下载）：编辑 `melo/text/japanese.py`：
```python
# 将这行：
_TAGGER = MeCab.Tagger()

# 改为懒加载：
_TAGGER = None

def _get_tagger():
    global _TAGGER
    if _TAGGER is None:
        _TAGGER = MeCab.Tagger()
    return _TAGGER

# 同时修改下方的调用：
def text2kata(text: str) -> str:
    parsed = _get_tagger().parse(text)  # 原先是 _TAGGER.parse(text)
```

> 注：这个修复已收录在 `references/melotts-mecab-fix.patch`，可用 `patch` 命令自动应用。

### 下载中文模型

MeloTTS 会在首次 `TTS(language='ZH')` 时自动下载模型文件（约 500MB）到 `~/.cache/`，需保持网络畅通。

### 测试合成

```bash
cd ~/hermes_data/melotts
source .venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com

python3 -c "
from melo.api import TTS
model = TTS(language='ZH', device='cpu')
speaker_id = model.hps.data.spk2id['ZH']
model.tts_to_file('你好，这是 MeloTTS 的中文语音测试。', speaker_id, 'test.wav')
"
```

### 合成参数调整

```python
model.tts_to_file(
    text, 
    speaker_id, 
    'output.wav',
    sdp_ratio=0.2,      # 语义分裂比例
    noise_scale=0.6,    # 噪声尺度
    noise_scale_w=0.8   # 韵律权重
)
```

### MeloTTS 与 Piper 中文效果对比

同一段 400+字的中文新闻播报：

| 指标 | Piper (huayan) | MeloTTS (ZH) | Edge TTS (Xiaoxiao) |
|:---|:---:|:---:|:---:|
| 音频时长 | 83.5s | 80.9s | 101.5s |
| 合成耗时 | 实时 | ~90s (CPU) | 秒回 |
| 语义断句 | 几乎没有 | 26 个语义单元 | 自然 |
| 韵律 | 机械平直 | 有停顿/呼吸感 | 最自然 |
| 音色 | 标准女声 | 偏播音腔 | 自然女声 |

> 💡 **总结**：若用户对 TTS 的 `断句` 或 `韵律` 表达不满（如"你这断句挺奇怪的"），MeloTTS 是比 Piper 更好的本地方案。

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

### Q11: Edge TTS 生成的中文语音只有 1-2 秒 / 报错 "No audio was received"

这是最常见的 Edge TTS 语言-语音不匹配问题。

**根本原因**：Hermes 默认的 Edge TTS voice 是 `en-US-AriaNeural`（纯英文语音），当输入中文文本时，服务端会直接拒绝或返回截断的空音频。

**快速判断**：
```bash
# 查看当前 Hermes 配置的 TTS provider 和 voice
hermes config | grep -A3 "tts"
```
如果显示 `provider: edge` 且 voice 是 `en-US-AriaNeural` / `en-GB` 等英文语音，中文文本一定会出问题。

**解决方案**（按优先级）：
1. **最佳**：部署本地 TTS。中文、有网 → 配置 Edge TTS 为中文语音 `zh-CN-XiaoxiaoNeural`；中文、离线 → 部署 MeloTTS（本 Skill Step 6）或 Piper（Step 2-4）
2. **次优**：切换到其他支持中文的云 TTS provider（如 ElevenLabs、MiniMax、OpenAI TTS，需要配置对应 API key）

### Q12: MeloTTS 安装时报错 `No such file or directory: requirements.txt`

PyPI 上的 `melotts` 包有构建缺陷，缺少 `requirements.txt`。

**解决**：从 GitHub 源码安装：
```bash
uv pip install git+https://github.com/myshell-ai/MeloTTS.git
```

### Q13: MeloTTS 运行时报错 `OSError: libcudart.so.13`

torchaudio 被安装为 CUDA 版本，但环境无 GPU。

**解决**：强制重新安装 CPU 版本：
```bash
uv pip install torchaudio --index-url https://download.pytorch.org/whl/cpu --force-reinstall
```

### Q14: MeloTTS 导入时报错 `RuntimeError: Failed initializing MeCab`

MeloTTS 的日语处理模块在导入时就初始化 MeCab Tagger，若 unidic 词典未就绪则抛出 RuntimeError。

**解决**：应用懒加载修复补丁（见本 Skill 的 `references/melotts-mecab-fix.patch`）：
```bash
cd ~/hermes_data/melotts/.venv/lib/python3.11/site-packages
patch -p2 < /path/to/melotts-mecab-fix.patch
```

或手动修改 `melo/text/japanese.py`：
1. 将 `_TAGGER = MeCab.Tagger()` 改为 `_TAGGER = None`
2. 添加 `_get_tagger()` 懒加载函数
3. 将 `parsed = _TAGGER.parse(text)` 改为 `parsed = _get_tagger().parse(text)`

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
- 本 Skill 附录：`references/post-processing.md` — 音频后处理命令（WAV转MP3等）
- 本 Skill 附录：`references/melotts-mecab-fix.patch` — MeloTTS 日语模块 MeCab 懒加载修复补丁
