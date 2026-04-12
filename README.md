# Mockingbird

<img src="src/assets/icon.png" alt="Mockingbird" width="120" align="right"/>

A desktop GUI for reference-based voice cloning powered by [VoxCPM2](https://github.com/OpenBMB/VoxCPM).

Import reference audio clips, type what you want them to say, and generate a cloned voice — all locally with no cloud dependency.

---

## Features

- **Voice library** — import `.wav` or `.mp3` files as named voices; files are stored locally, `.mp3` files are auto-converted on use
- **Per-voice settings** — CFG value, inference steps, and denoiser toggle saved per voice; switching voices automatically restores their settings
- **Audio playback** — listen to generated output directly in the app
- **File naming** — rename generated files inline; AI auto-names files when Ollama is enabled (max 5 words)
- **Library view** — browse all generated files with voice and text info, filter by voice, play or delete entries
- **GPU acceleration** — uses CUDA automatically if an NVIDIA GPU is available, falls back to CPU
- **Model caching** — model loads in the background at startup and stays in memory, so subsequent generations run without reload delay
- **Optional AI prompt panel** — connect to a local [Ollama](https://ollama.com) server to generate text that auto-fills the "Text to Speak" box

---

## Requirements

- Python 3.11+
- PyTorch with CUDA support (recommended for GPU acceleration):
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
- [Ollama](https://ollama.com) (optional, for AI prompt and auto-naming)

Install remaining Python dependencies:

```bash
pip install pyqt6 voxcpm soundfile requests imageio-ffmpeg
```

> FFmpeg is bundled via `imageio-ffmpeg` — no separate system install required.

---

## Usage

```bash
python main.py
```

### Basic workflow

1. Go to the **Voices** tab and click **Add Voice** to import a `.wav` or `.mp3` reference file, then give it a display name
2. Switch to the **Generate** tab and select your voice from the dropdown
3. Type the text you want spoken in the **Text to Speak** box
4. Adjust **CFG Value**, **Inference Steps**, and **Use Denoiser** as desired
5. Click **Generate** — the output is saved to `output/` and playback controls appear
6. Rename the file using the filename field below the player, or let AI name it automatically

### Library

Switch to the **Library** tab to see all generated files. Each entry shows the filename, reference voice, and a preview of the spoken text. Use the **Filter by voice** dropdown to narrow the list. Click **▶** to play or **✕** to delete.

### AI assistant (optional)

1. Open **Settings → AI Settings...**
2. Enter your Ollama host and port, click **Connect**, and select a model
3. Check **Enable AI Assistant** and click **Save**
4. The **AI Prompt** panel appears above the text box — describe what you want the AI to write, click **Ask AI**, and the result is placed into "Text to Speak" automatically
5. After each generation, the AI will suggest a short filename (up to 5 words) and rename the file automatically

---

## Voice Settings

| Setting | Default | Description |
|---|---|---|
| CFG Value | 2.0 | Classifier-free guidance scale (0.1 – 10.0). Higher = more faithful to the reference style |
| Inference Steps | 10 | Diffusion sampling steps. More steps = slower but potentially cleaner output |
| Use Denoiser | Off | Apply a post-processing denoiser to the output |

Settings are saved per voice. Switching to a different voice restores that voice's last-used settings.

---

## Credits

Voice cloning model: [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB
