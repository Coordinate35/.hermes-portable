@echo off
chcp 65001 >nul
echo ==========================================
echo    ChatTTS 语音服务 - 一键安装脚本
echo ==========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python。请先安装 Python 3.9+ 并添加到 PATH。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python 版本:
python --version
echo.

:: 创建虚拟环境
echo [2/4] 创建虚拟环境 venv_chattts ...
if exist venv_chattts (
    echo        虚拟环境已存在，跳过创建。
) else (
    python -m venv venv_chattts
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败。
        pause
        exit /b 1
    )
)
echo.

:: 激活并安装依赖
echo [3/4] 安装依赖包（约需 2-5 分钟，取决于网速）...
call venv_chattts\Scripts\activate.bat

python -m pip install --upgrade pip

:: 先装 torch（带 CUDA 支持）
echo        安装 PyTorch (CUDA 12.1) ...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 安装 ChatTTS 和 Flask
echo        安装 ChatTTS + Flask ...
pip install ChatTTS flask

if errorlevel 1 (
    echo [错误] 安装依赖失败，请检查网络连接。
    pause
    exit /b 1
)
echo.

:: 启动服务
echo [4/4] 启动 ChatTTS 语音服务 ...
echo        服务将监听 0.0.0.0:5000
echo        按 Ctrl+C 停止服务
echo        首次启动会自动下载模型（约 3-4GB，请耐心等待）
echo.
echo ==========================================
echo    服务地址: http://宿主机IP:5000
echo    虚拟机内访问: http://10.0.2.2:5000
echo ==========================================
echo.

python chattts_server.py

pause
