# Voice Design Spec — VoxCPM TTS.py

**Date:** 2026-04-10  
**Status:** Approved

## Goal

A minimal personal-use script that generates a `.wav` file from text using VoxCPM2's text-only voice design (no reference audio required).

## Configuration

Three constants at the top of `TTS.py` control all behaviour:

```python
VOICE  = "A young woman, gentle and sweet voice"
TEXT   = "Hello, this is a test."
OUTPUT = "output.wav"
```

- `VOICE` — natural language description injected as `(...)` prefix on the text
- `TEXT` — the words to synthesize
- `OUTPUT` — path for the saved `.wav` file

## Architecture

Single flat script, top-to-bottom execution. No functions, no classes.

1. Import `VoxCPM` and `soundfile`
2. Define constants (`VOICE`, `TEXT`, `OUTPUT`)
3. Load model: `VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)`
4. Build prompt: `f"({VOICE}){TEXT}"`
5. Generate: `model.generate(text=prompt, cfg_value=2.0, inference_timesteps=10)`
6. Save: `sf.write(OUTPUT, wav, model.tts_model.sample_rate)`

## Key Parameters

| Parameter | Value | Note |
|---|---|---|
| `cfg_value` | `2.0` | How strictly the voice description is enforced |
| `inference_timesteps` | `10` | Speed/quality trade-off; increase for better quality |
| `load_denoiser` | `False` | Faster inference, negligible quality difference |

## Out of Scope

- CLI input, batch processing, streaming, reference audio cloning
