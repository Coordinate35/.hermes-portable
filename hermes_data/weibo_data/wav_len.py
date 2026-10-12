#!/usr/bin/env python3
import wave

w = wave.open("/tmp/weibo_voice.wav")
print("channels", w.getnchannels(), "sampwidth", w.getsampwidth(),
      "rate", w.getframerate(), "frames", w.getnframes())
print("seconds:", round(w.getnframes() / w.getframerate(), 1))
