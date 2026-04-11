# Mockingbird

A desktop GUI for reference-based voice cloning powered by [VoxCPM2](https://github.com/OpenBMB/VoxCPM).

Upload a reference audio clip, type what you want it to say, and generate a cloned voice — all from a simple local app with no cloud dependency.

---

## Features

- **Reference audio selection** — browse for any `.wav` or `.mp3` file; `.mp3` files are auto-converted
- **Recent references** — last 10 used files remembered across sessions
- **Per-voice settings** — CFG value, inference steps, and denoiser toggle saved per reference file; switching voices automatically restores their settings
- **Audio playback** — listen to generated output directly in the app
- **File naming** — rename generated files inline; AI auto-names files when Ollama is enabled (max 5 words)
- **Library view** — browse all generated files with voice and text info, filter by voice, and play or delete entries
- **GPU acceleration** — uses CUDA automatically if an NVIDIA GPU is available, falls back to CPU
- **Optional AI prompt panel** — connect to a local [Ollama](https://ollama.com) server to generate text that auto-fills the "Text to Speak" box

---

## Requirements

- Python 3.11+
- [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` (for MP3 conversion)
- PyTorch with CUDA support (recommended for GPU acceleration):
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
- [Ollama](https://ollama.com) (optional, for AI prompt and auto-naming)

Install remaining Python dependencies:

```bash
pip install pyqt6 voxcpm soundfile requests imageio-ffmpeg
```

---

## Usage

```bash
python main.py
```

### Basic workflow

1. Click **Browse** to select a reference `.wav` or `.mp3` file
2. Type the text you want spoken in the **Text to Speak** box
3. Adjust **CFG Value**, **Inference Steps**, and **Use Denoiser** as desired
4. Click **Generate** — the output is saved to `output/` and playback controls appear
5. Rename the file using the filename field below the player, or let AI name it automatically

### Library

Switch to the **Library** tab to see all generated files. Each entry shows the filename, reference voice, and a preview of the spoken text. Use the **Filter by voice** dropdown to narrow the list. Click **▶** to play or **✕** to delete.

### AI assistant (optional)

1. Open **Settings → AI Settings...**
2. Enter your Ollama host and port, click **Connect**, and select a model
3. Check **Enable AI Assistant** and click **Save**
4. The **AI Prompt** panel appears above the text box — describe what you want the AI to write, click **Ask AI**, and the result is placed into "Text to Speak" automatically
5. After each generation, the AI will also suggest a short filename (up to 5 words) and rename the file automatically

---

## Voice Settings

| Setting | Default | Description |
|---|---|---|
| CFG Value | 2.0 | Classifier-free guidance scale (0.1 – 10.0). Higher = more faithful to the reference style |
| Inference Steps | 10 | Diffusion sampling steps. More steps = slower but potentially cleaner output |
| Use Denoiser | Off | Apply a post-processing denoiser to the output |

Settings are saved per reference voice. Switching to a different voice restores that voice's last-used settings.

---

## Credits

Voice cloning model: [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB
