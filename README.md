<div align="center">

<img src="src/assets/icon.png" width="96" alt="Mockingbird"/>

# Mockingbird

**Local, offline voice cloning desktop app powered by VoxCPM2**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41cd52?style=flat-square)](https://pypi.org/project/PyQt6/)
[![Model](https://img.shields.io/badge/Model-VoxCPM2-e8a838?style=flat-square)](https://github.com/OpenBMB/VoxCPM)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Offline](https://img.shields.io/badge/Runs-100%25%20Locally-success?style=flat-square)](#)

</div>

---

## What is Mockingbird?

Mockingbird is a desktop GUI for reference-based voice cloning. Import any short audio clip as a voice reference, type what you want it to say, and generate a cloned voice — entirely on your own machine, with no cloud dependency.

---

## Features

| | Feature | Description |
|---|---|---|
| 🎙️ | **Voice library** | Import `.wav` or `.mp3` files as named voices, stored locally |
| 🎛️ | **Per-voice settings** | CFG value, inference steps, and denoiser saved per voice |
| ▶️ | **Playback** | Listen to generated output directly in the app |
| 🏷️ | **File naming** | Rename outputs inline, or let AI name them automatically |
| 📚 | **Library** | Browse, filter, play and delete all generated files |
| ⚡ | **Model caching** | Model loads once at startup and stays warm — no reload delay |
| 🖥️ | **GPU acceleration** | CUDA used automatically when available, falls back to CPU |
| 🤖 | **AI assistant** | Optional Ollama integration for prompt generation and auto-naming |

---

## Getting Started

### Requirements

- **Python 3.11+**
- **PyTorch** — with CUDA for GPU acceleration (recommended):
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
- **[Ollama](https://ollama.com)** *(optional)* — for AI prompt generation and auto-naming

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Marijn-Deijnen/Mockingbird.git
cd Mockingbird

# 2. Install dependencies
pip install pyqt6 voxcpm soundfile requests imageio-ffmpeg

# 3. Run
python main.py
```

> FFmpeg is bundled via `imageio-ffmpeg` — no separate system install required.

---

## Usage

### Basic workflow

```
Voices tab → Add Voice → Import a .wav or .mp3 and give it a name
     ↓
Generate tab → Select voice → Type text → Adjust settings → Generate
     ↓
Output appears with playback controls — rename inline or let AI name it
     ↓
Library tab → Browse, filter, replay, or delete past generations
```

### Voice Settings

| Setting | Default | Description |
|---|---|---|
| **CFG Value** | `2.0` | Classifier-free guidance scale `(0.1 – 10.0)`. Higher = more faithful to reference style |
| **Inference Steps** | `10` | Diffusion sampling steps. More steps = slower but potentially cleaner output |
| **Use Denoiser** | Off | Apply a post-processing denoiser pass to the output |

Settings are saved per voice and restored automatically when you switch voices.

### AI Assistant *(optional)*

1. Open the **Settings** tab
2. Enter your Ollama host and port, click **Connect**, and select a model
3. Enable the **Enable AI features** toggle
4. Enable **Show AI Prompt panel** to show the prompt box in the Generate tab
5. Describe what you want the AI to say → click **Ask AI** → result fills the text box
6. After each generation the AI also suggests a filename (up to 5 words) automatically

---

## Credits

Voice cloning model: [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by [OpenBMB](https://github.com/OpenBMB)
