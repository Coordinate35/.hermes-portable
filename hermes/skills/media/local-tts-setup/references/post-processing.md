# Piper TTS 常用后处理命令

## WAV 转 MP3（压缩发送）

```bash
ffmpeg -y -i input.wav -codec:a libmp3lame -q:a 4 output.mp3
```

参数说明：
- `-y`：覆盖输出文件
- `-codec:a libmp3lame`：使用 LAME MP3 编码器
- `-q:a 4`：VBR 音质等级（4=较好，2=很好，0=极致）

实际效果：3.6MB WAV → 585KB MP3，音质无明显损失。