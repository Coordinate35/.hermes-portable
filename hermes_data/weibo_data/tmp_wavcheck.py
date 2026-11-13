import wave
w = wave.open('/tmp/weibo_voice.wav')
print("dur=%.1fs rate=%d ch=%d frames=%d" % (w.getnframes()/w.getframerate(), w.getframerate(), w.getnchannels(), w.getnframes()))
