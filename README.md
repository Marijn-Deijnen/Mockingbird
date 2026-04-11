# Mockingbird

A desktop GUI for reference-based voice cloning powered by [VoxCPM2](https://github.com/OpenBMB/VoxCPM).

Upload a reference audio clip, type what you want it to say, and generate a cloned voice — all from a simple local app with no cloud dependency.

---

## Features

- **Reference audio selection** — browse for any `.wav` or `.mp3` file; `.mp3` files are auto-converted
- **Recent references** — last 10 used files remembered across sessions
- **Voice settings** — CFG value, inference steps, and optional denoiser, all adjustable with linked sliders
- **Audio playback** — listen to generated output directly in the app
- **Output saving** — generated audio saved to `output/` with a timestamped filename
- **Optional AI prompt panel** — connect to a local [Ollama](https://ollama.com) server to generate text that auto-fills the "Text to Speak" box

---

## Requirements

- Python 3.11+
- [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` (for MP3 conversion)
- [Ollama](https://ollama.com) (optional, for the AI prompt feature)

Install Python dependencies:

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

### AI prompt (optional)

1. Open **Settings → AI Settings...**
2. Enter your Ollama host and port, click **Connect**, and select a model
3. Check **Enable AI Assistant** and click **Save**
4. The **AI Prompt** panel appears above the text box — describe what you want the AI to write, click **Ask AI**, and the result is placed into "Text to Speak" automatically

---

## Voice Settings

| Setting | Default | Description |
|---|---|---|
| CFG Value | 2.0 | Classifier-free guidance scale (0.1 – 10.0). Higher = more faithful to the reference style |
| Inference Steps | 10 | Diffusion sampling steps. More steps = slower but potentially cleaner output |
| Use Denoiser | Off | Apply a post-processing denoiser to the output |

---

## Project Structure

```
main.py                        # Entry point
src/
  app.py                       # MainWindow — layout and signal wiring
  config.py                    # Load/save config.json
  audio.py                     # WAV conversion and output path helpers
  model.py                     # GenerationWorker (QThread wrapping VoxCPM2)
  ollama.py                    # fetch_models() + OllamaWorker (QThread)
  widgets/
    reference_panel.py         # Reference audio selection panel
    text_panel.py              # Text to Speak input
    settings_panel.py          # CFG/steps/denoiser controls
    output_panel.py            # Generate/Play/Stop buttons and progress
    ai_panel.py                # AI Prompt panel (shown when Ollama enabled)
  dialogs/
    settings_dialog.py         # AI Settings dialog
tests/
  test_audio.py
  test_config.py
  test_ollama.py
output/                        # Generated audio files (gitignored)
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Credits

Voice cloning model: [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB
