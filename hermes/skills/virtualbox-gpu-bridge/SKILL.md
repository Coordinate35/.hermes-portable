---
name: virtualbox-gpu-bridge
description: 解决 VirtualBox 虚拟机无法直接使用宿主机 NVIDIA GPU 的问题，通过在宿主机运行 GPU 服务 + 虚拟机通过 NAT 网络调用的 HTTP API 模式。包含完整的 ChatTTS 部署示例和可复用的模板代码，适用于 TTS、图像生成、LLM 等任何 GPU 加速场景。
title: VirtualBox GPU Bridge - 虚拟机调用宿主机 GPU 服务
trigger: |
  用户在 VirtualBox 虚拟机里想使用宿主机 GPU；
  VirtualBox 不支持 NVIDIA GPU 直通；
  需要在虚拟机内调用宿主机上的 AI/ML 服务（TTS、图像生成、LLM 等）；
  10.0.2.2 NAT 访问宿主机服务；
  为虚拟机暴露宿主机本地服务。
---

# VirtualBox GPU Bridge

## 快速决策：GPU 可用 vs 不可用

检查 GPU 可用性（虚拟机内执行）：
```bash
python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "no PyTorch"
# 或
lspci | grep -i nvidia
nvidia-smi 2>/dev/null || echo "no nvidia-smi"
```

| 结果 | 推荐方案 |
|:---|:---|
| **GPU 可用** → 需要极致自然度 | 继续本 Skill 主体：宿主机跑 ChatTTS GPU 服务 + 虚拟机调用 |
| **GPU 不可用** → 只需基本播报 | 转到 **local-tts-setup** Skill：虚拟机内纯 CPU 安装 **Piper**（轻量、离线、实时） |

## 核心问题

VirtualBox **原生不支持 NVIDIA CUDA GPU 直通**到虚拟机。无论怎么配置，虚拟机内的 `lspci`、`nvidia-smi`、`torch.cuda.is_available()` 都检测不到 GPU。

## 解决方案：宿主机服务 + 虚拟机客户端

在**宿主机**上运行带 GPU 加速的服务，通过 **HTTP API** 暴露给虚拟机调用。

### 网络拓扑（NAT 模式）

```
宿主机 (Windows/Linux, 有 GPU)
  └─ Python HTTP 服务 @ 0.0.0.0:5000
        ↑
        │ VirtualBox NAT
        │ 宿主机对虚拟机暴露为 10.0.2.2
        ↓
虚拟机 (Linux, 无 GPU)
  └─ Python 客户端调用 http://10.0.2.2:5000
```

**关键知识点**：VirtualBox NAT 模式下，虚拟机访问 `10.0.2.2` 即宿主机。

## 通用部署模板

### 1. 宿主机防火墙放行

**Windows（管理员 PowerShell）：**
```powershell
netsh advfirewall firewall add rule name="GPU Service" dir=in action=allow protocol=tcp localport=5000
```

**Linux：**
```bash
sudo ufw allow 5000/tcp
# 或
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### 2. 宿主机服务模板

创建 `gpu_server.py`：

```python
from flask import Flask, request, jsonify
import torch

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    })

# 你的 GPU 推理端点
@app.route("/infer", methods=["POST"])
def infer():
    data = request.get_json()
    # ... GPU 推理逻辑 ...
    return jsonify({"result": "..."})

if __name__ == "__main__":
    # 必须监听 0.0.0.0，否则虚拟机无法访问
    app.run(host="0.0.0.0", port=5000)
```

**启动服务**：
```bash
python gpu_server.py
```

### 3. 虚拟机客户端模板

```python
import urllib.request, json

HOST = "10.0.2.2"  # VirtualBox NAT 下宿主机的固定地址
PORT = 5000

def call_api(path, data=None):
    url = f"http://{HOST}:{PORT}{path}"
    if data:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()

# 测试
print(call_api("/health"))
```

## 完整示例：ChatTTS 语音服务

以下是一个完整的、经过验证的 ChatTTS 部署包，适用于 Windows 宿主机 + Linux 虚拟机。

### 文件清单

| 文件 | 运行位置 | 说明 |
|:---|:---|:---|
| `setup.bat` | 宿主机 | 一键安装环境并启动服务 |
| `chattts_server.py` | 宿主机 | Flask HTTP 服务 |
| `tts_client.py` | 虚拟机 | 调用宿主机服务 |

### setup.bat（Windows 宿主机）

```batch
@echo off
chcp 65001 >nul

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python。请先安装 Python 3.9+。
    pause
    exit /b 1
)

if exist venv_chattts (
    echo 虚拟环境已存在，跳过创建。
) else (
    python -m venv venv_chattts
)

call venv_chattts\Scripts\activate.bat
python -m pip install --upgrade pip

:: 安装 CUDA 版 PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 安装 ChatTTS + Flask
pip install ChatTTS flask

echo.
echo 启动服务...
echo 首次启动会自动下载模型（约 3-4GB）
echo 虚拟机访问地址: http://10.0.2.2:5000
python chattts_server.py
pause
```

### chattts_server.py（精简版）

```python
from flask import Flask, request, jsonify, send_file
import ChatTTS, torch, torchaudio, numpy as np, tempfile, time

app = Flask(__name__)
chat_tts = None
model_loaded = False

def load_model():
    global chat_tts, model_loaded
    if model_loaded:
        return True
    chat_tts = ChatTTS.Chat()
    chat_tts.load(compile=False)
    model_loaded = True
    return True

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "model_loaded": model_loaded
    })

@app.route("/tts", methods=["POST"])
def tts():
    if not load_model():
        return jsonify({"error": "模型加载失败"}), 500

    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text 不能为空"}), 400

    # 设置随机种子
    seed = data.get("audio_seed")
    if seed is not None:
        torch.manual_seed(int(seed))

    params = {
        "prompt": "",
        "temperature": float(data.get("temperature", 0.3)),
        "top_P": float(data.get("top_P", 0.7)),
        "top_K": int(data.get("top_K", 20)),
    }

    wavs = chat_tts.infer([text], params_infer_code=params)
    wav = wavs[0]

    if isinstance(wav, np.ndarray):
        wav_tensor = torch.from_numpy(wav).unsqueeze(0)
    else:
        wav_tensor = wav.unsqueeze(0) if wav.dim() == 1 else wav

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name

    torchaudio.save(temp_path, wav_tensor, 24000)
    return send_file(temp_path, mimetype="audio/wav")

if __name__ == "__main__":
    print("ChatTTS Server @ http://0.0.0.0:5000")
    print("虚拟机访问: http://10.0.2.2:5000")
    app.run(host="0.0.0.0", port=5000)
```

### tts_client.py（虚拟机内）

```python
#!/usr/bin/env python3
import sys, json, urllib.request

HOST = "10.0.2.2"
PORT = 5000

def tts(text, output="output.wav", seed=42):
    url = f"http://{HOST}:{PORT}/tts"
    data = json.dumps({"text": text, "audio_seed": seed}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(output, "wb") as f:
            f.write(resp.read())
    print(f"已保存: {output}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 tts_client.py '你好，世界'")
        sys.exit(1)
    tts(sys.argv[1])
```

## 关键配置检查清单

- [ ] 宿主机防火墙放行目标端口（5000）
- [ ] Flask 服务监听 `0.0.0.0` 而不是 `127.0.0.1`
- [ ] 虚拟机内通过 `10.0.2.2` 访问（NAT 模式）
- [ ] 如果 VirtualBox 使用桥接模式，则用宿主机真实局域网 IP
- [ ] 服务黑窗口/进程保持运行，不要关闭

## 常见问题

### Q: 虚拟机访问 10.0.2.2:5000 超时？
- 检查宿主机防火墙是否放行 5000 端口
- 检查服务是否监听 `0.0.0.0:5000`
- 检查 VirtualBox 网络适配器是否为 NAT

### Q: CUDA 不可用？
- 这是预期行为。VirtualBox 不支持 GPU 直通。
- 确保宿主机安装了 NVIDIA 驱动和 CUDA Toolkit
- 宿主机上运行 `python -c "import torch; print(torch.cuda.is_available())"` 应返回 True

### Q: 模型下载慢？
- ChatTTS 首次会自动从 HuggingFace 下载模型
- 可以预先下载模型放到 `~/.cache/chattts/` 或指定本地路径

## 扩展到其他场景

这个架构模式（宿主机 GPU 服务 + 虚拟机 HTTP 客户端）可以复用于：

- **Stable Diffusion**：宿主机跑 ComfyUI/Automatic1111，虚拟机调用文生图 API
- **本地 LLM**：宿主机跑 ollama/vLLM，虚拟机通过 OpenAI-compatible API 调用
- **Whisper 语音识别**：宿主机跑 faster-whisper，虚拟机上传音频文件获取转录
- **任何 PyTorch/TensorFlow GPU 任务**

## 参考资源

- VirtualBox NAT 网络文档：https://www.virtualbox.org/manual/ch06.html#network_nat
- ChatTTS GitHub：https://github.com/2noise/ChatTTS
- VirtualBox 官方不支持 GPU 直通声明（仅 experimental PCI passthrough 对 Linux 宿主机）
