# VoxCPM GUI — Design Spec
**Date:** 2026-04-11

## Overview

A PyQt6 desktop application that wraps the VoxCPM2 voice cloning model. The user selects a reference audio file, enters text, tweaks generation parameters, and generates a cloned-voice audio file — all without touching Python scripts.

## Scope

- Reference-audio-based voice cloning only (no voice design / text-description mode)
- Replaces the standalone `borat.py` and `optimus.py` scripts entirely

## Package Structure

```
E:/Coding/VoxCPM/
├── main.py                       # Entry point — creates QApplication, launches MainWindow
├── src/
│   ├── __init__.py
│   ├── app.py                    # MainWindow: assembles panels, wires signals/slots
│   ├── config.py                 # Loads/saves config.json (persistent settings)
│   ├── audio.py                  # mp3→wav conversion via imageio_ffmpeg, output path logic
│   ├── model.py                  # VoxCPM model wrapper and QThread generation worker
│   └── widgets/
│       ├── __init__.py
│       ├── reference_panel.py    # File picker + recent references list (up to 10)
│       ├── text_panel.py         # Multiline text input
│       ├── settings_panel.py     # Sliders + checkbox for generation parameters
│       └── output_panel.py       # Generate button, progress bar, playback controls, output path label
├── audio/                        # Reference audio files
├── output/                       # Generated .wav files (timestamped filenames)
└── config.json                   # Runtime-persisted settings
```

## Modules

### `config.py`
Reads and writes `config.json` at the project root. Persisted fields:
- `last_reference` — absolute path of the last selected reference file
- `recent_references` — list of up to 10 recent reference file paths (most recent first)
- `cfg_value` — float, default 2.0
- `inference_timesteps` — int, default 10
- `use_denoiser` — bool, default false

On first run (no `config.json`), all defaults apply.

### `audio.py`
- `ensure_wav(path: str) -> str` — if the file is `.mp3`, converts to `.wav` alongside the original using `imageio_ffmpeg`. Returns the `.wav` path. No-op if already `.wav`.
- `output_path() -> str` — returns `output/YYYY-MM-DD_HHMMSS.wav`, creating the `output/` directory if needed.

### `model.py`
- `ModelWorker(QThread)` — loads `VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=<bool>)` and calls `model.generate(text, reference_wav_path, cfg_value, inference_timesteps)`. Emits `finished(wav, sample_rate)` on success and `error(message)` on failure.
- Model is loaded once per generation run (not cached between runs) to keep memory usage predictable. If this proves slow in practice, lazy caching can be added later.

### `widgets/reference_panel.py`
- "Browse" button opens a `QFileDialog` filtered to `.wav` and `.mp3` files.
- Selected path is displayed inline and added to the recent list in `config.json`.
- Recent references shown as clickable labels (up to 10); clicking one sets it as the active reference.

### `widgets/text_panel.py`
- `QPlainTextEdit` for multiline text input.
- No persistence between sessions (intentional — text is ephemeral).

### `widgets/settings_panel.py`
Three controls:
| Control | Widget | Range | Default |
|---|---|---|---|
| CFG Value | `QDoubleSpinBox` + `QSlider` (linked) | 0.1 – 10.0, step 0.1 | 2.0 |
| Inference Steps | `QSpinBox` + `QSlider` (linked) | 1 – 100, step 1 | 10 |
| Use Denoiser | `QCheckBox` | — | unchecked |

Slider and spinbox are bidirectionally linked (changing one updates the other). Values are saved to `config.json` on change.

### `widgets/output_panel.py`
- **Generate** button: disabled while generation is in progress.
- **Progress bar**: indeterminate pulse while generating; 100% on completion; hidden when idle.
- **Play / Stop** buttons: use `QMediaPlayer` to play the last generated `.wav`. Disabled until a file has been generated this session.
- **Output path label**: displays the path of the last generated file.

### `app.py`
`MainWindow` stacks the four panels vertically using `QVBoxLayout`. Wires signals:
- Reference panel → updates active reference path in config
- Generate button → creates `ModelWorker`, starts thread
- `ModelWorker.finished` → writes wav via `soundfile`, updates output label, enables playback
- `ModelWorker.error` → shows `QMessageBox` with error text
- Settings changes → immediately persisted via `config.py`

## UI Layout

```
┌─────────────────────────────────────────────┐
│  Reference Audio                            │
│  [Browse...]  path/to/file.wav              │
│  Recent:  borat.mp3  |  optimus.mp3  | ...  │
├─────────────────────────────────────────────┤
│  Text to Speak                              │
│  ┌─────────────────────────────────────┐   │
│  │ (multiline text input)              │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│  Voice Settings                             │
│  CFG Value          [====|----]  2.0        │
│  Inference Steps    [==|------]  10         │
│  Use Denoiser       [ ] (checkbox)          │
├─────────────────────────────────────────────┤
│  Output                                     │
│  [  Generate  ]   [▶ Play]   [■ Stop]       │
│  ████████░░░░░░░  Generating...             │
│  output/2026-04-11_143022.wav               │
└─────────────────────────────────────────────┘
```

## Persistence

`config.json` is read on startup and written on every relevant change (reference selection, slider adjustment, checkbox toggle). The app does not require an explicit "Save" action.

## Output Files

Generated files are saved to `output/YYYY-MM-DD_HHMMSS.wav`. The `output/` directory is created automatically. Files are never overwritten.

## Error Handling

- If no reference audio is selected when Generate is pressed: show inline warning label, do not start generation.
- If text input is empty: same — inline warning, no generation.
- If model loading or generation fails: `QMessageBox.critical` with the exception message.
- If output directory cannot be created: surface the OS error in a `QMessageBox`.

## Dependencies

All already present in the project environment:
- `PyQt6`
- `voxcpm`
- `soundfile`
- `imageio_ffmpeg`
