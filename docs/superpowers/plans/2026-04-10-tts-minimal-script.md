# TTS Minimal Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a single `TTS.py` script that generates a `.wav` file from text using VoxCPM2 voice design with no reference audio.

**Architecture:** Flat top-to-bottom script. Three constants (`VOICE`, `TEXT`, `OUTPUT`) are defined at the top. The voice description is injected as a `(...)` prefix on the text before being passed to the model.

**Tech Stack:** Python 3.10+, `voxcpm`, `soundfile`

---

### Task 1: Install dependencies

**Files:**
- No file changes — environment setup only

- [ ] **Step 1: Install required packages**

```bash
pip install voxcpm soundfile
```

Expected output: Successfully installed packages (or "already satisfied").

- [ ] **Step 2: Verify imports work**

```bash
python -c "from voxcpm import VoxCPM; import soundfile; print('OK')"
```

Expected output: `OK`

---

### Task 2: Write TTS.py

**Files:**
- Create: `TTS.py`

- [ ] **Step 1: Verify the prompt format is correct before writing the full script**

Run this one-liner to confirm the `(voice)text` format works as expected:

```bash
python -c "
VOICE = 'A young woman, gentle and sweet voice'
TEXT = 'Hello, this is a test.'
prompt = f'({VOICE}){TEXT}'
assert prompt == '(A young woman, gentle and sweet voice)Hello, this is a test.'
print('Prompt format OK:', prompt)
"
```

Expected output:
```
Prompt format OK: (A young woman, gentle and sweet voice)Hello, this is a test.
```

- [ ] **Step 2: Create TTS.py**

```python
from voxcpm import VoxCPM
import soundfile as sf

# --- Configuration ---
VOICE  = "A young woman, gentle and sweet voice"
TEXT   = "Hello, this is a test."
OUTPUT = "output.wav"

# --- Generation ---
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)

prompt = f"({VOICE}){TEXT}"
wav = model.generate(text=prompt, cfg_value=2.0, inference_timesteps=10)

sf.write(OUTPUT, wav, model.tts_model.sample_rate)
print(f"Saved to {OUTPUT}")
```

- [ ] **Step 3: Run the script**

```bash
python TTS.py
```

Expected output:
```
Saved to output.wav
```

Also verify `output.wav` exists and is non-empty:

```bash
python -c "import os; size = os.path.getsize('output.wav'); print(f'output.wav: {size} bytes'); assert size > 1000, 'File too small'"
```

Expected: `output.wav: XXXXX bytes` (should be tens of kilobytes or more)

- [ ] **Step 4: Commit**

```bash
git init
git add TTS.py
git commit -m "feat: add minimal VoxCPM2 TTS script with text-only voice design"
```

---

## Changing the Voice

To use a different voice, edit the `VOICE` constant at the top of `TTS.py`. Examples:

```python
VOICE = "An elderly man, deep and gravelly voice"
VOICE = "A cheerful young boy, fast and energetic"
VOICE = "A calm middle-aged woman, slow and soothing"
```

To change the output text, edit `TEXT`. To change the output filename, edit `OUTPUT`.
