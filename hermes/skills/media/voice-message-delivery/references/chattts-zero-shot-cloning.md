# ChatTTS Zero-shot Voice Cloning

## Verified Facts (from source code inspection of 2noise/ChatTTS, 39.2k stars, 2026-05-17)

### What ChatTTS CAN do (zero-shot cloning)

ChatTTS supports **zero-shot speaker cloning** via the DVAE encoder. No training required.

```python
import ChatTTS
import torchaudio

chat = ChatTTS.Chat()
chat.load(compile=False)  # compile=True for better perf, but compile=False is safer

# 1. Load reference audio (your own voice or someone else's)
wav, sr = torchaudio.load("reference.wav")

# 2. Extract speaker embedding via DVAE encoder
spk_prompt = chat.sample_audio_speaker(wav.squeeze().numpy())
#    ^-- internally calls: self.dvae.sample_audio(wav) -> self(wav, "encode")

# 3. Generate new speech with the cloned voice
params = ChatTTS.Chat.InferCodeParams(spk_smp=spk_prompt)
wavs = chat.infer(["这是一段测试文本"], params_infer_code=params)

# Save
import torch
import numpy as np
torchaudio.save("output.wav", torch.from_numpy(wavs[0]).unsqueeze(0), 24000)
```

### How it works (code path)

1. `chat.sample_audio_speaker(wav)` -> `Speaker.encode_prompt(DVAE.sample_audio(wav))`
2. `DVAE.sample_audio(wav)` -> `self(wav, "encode")` -> produces speaker prompt tensor
3. During `chat.infer()`, if `params.spk_smp is not None`:
   - `Speaker.decode_prompt(params.spk_smp)` decodes the compressed prompt
   - The prompt is injected into the GPT input embeddings where `input_ids.eq(spk_emb_ids)`
   - This conditions the generation on the reference speaker's timbre

### Windows Compatibility

| Feature | Windows Support | Notes |
|:---|:---:|:---|
| Inference / Zero-shot cloning | Yes | Pure PyTorch, no special deps |
| `compile=True` | Maybe | `torch.compile` support varies by PyTorch version on Windows |
| vLLM acceleration | No | Official docs: "Linux only" |
| TransformerEngine | No | Official docs: "Linux only" |
| FlashAttention-2 | Optional | Docs warn "DO NOT INSTALL" — it currently slows generation down |
| Training / Fine-tuning | No | No official training code released |

### Key Parameters

- `spk_emb` — a pre-saved speaker embedding string (from `sample_random_speaker()`)
- `spk_smp` — a speaker prompt extracted from an audio file (from `sample_audio_speaker()`)
- `txt_smp` — text sample paired with audio (rarely used)

Use `spk_smp` for zero-shot cloning from reference audio. Use `spk_emb` for reusing a previously saved random speaker.

### Model Limitations

1. **Noise artifacts**: The 40k-hour pretrained model has intentional high-frequency noise + MP3 compression, as an anti-abuse measure. Cloned voices inherit this.
2. **Accuracy**: Zero-shot captures "rough timbre" — gender, age range, general vocal quality. It does NOT capture fine-grained nuances, emotional range, or speaking style as well as trained models like GPT-SoVITS.
3. **Reference audio**: Recommend 3–10 seconds of clean speech. Background noise, music, or very short clips degrade quality.

### Alternatives for Higher Precision

| Tool | Training Required | Windows | Fidelity | Best For |
|:---|:---:|:---:|:---:|:---|
| ChatTTS (zero-shot) | No | Yes | Medium | Quick prototyping,对话场景 |
| GPT-SoVITS | Yes (fine-tune) | Yes | High | 高精度声音克隆 |
| RVC | Yes (training) | Yes | High | 实时语音转换、唱歌 |
| Fish Speech | No (zero-shot) | Yes | Medium-High | 多语言TTS |
