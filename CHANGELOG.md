# Changelog

All notable changes to Mockingbird are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — 2026-04-13

### Added
- **Style prefix** — set a tone/emotion/pace description (e.g. `cheerful, slightly faster`) in General Settings; it is automatically prepended to generated text as `(prefix)text` on every generation
- **Auto-play on complete** — toggle in General Settings to automatically play generated audio when synthesis finishes
- **AI System Prompt** — editable system prompt for the Ollama AI assistant (visible in General Settings when AI is enabled); supports a `{voice_name}` placeholder that is substituted with the currently selected voice at request time
- **General Settings** — renamed from "Generate Tab" to "General Settings" to better reflect the scope of options it contains

---

## [1.0.0] — 2026-04-13

Initial release.

### Added
- **Voice library** — import `.wav` / `.mp3` files as named voices; files stored locally in `audio/`
- **Voice selector** — pick any managed voice as the cloning reference
- **Text-to-speech generation** — powered by VoxCPM2 via reference-based voice cloning
- **Per-voice settings** — CFG value, inference steps, and denoiser toggle saved per voice and restored on switch
- **Output playback** — listen to generated audio directly in the app
- **Inline file renaming** — rename generated files from the output panel
- **Library view** — browse all past generations with voice and text info; filter by voice, play, or delete entries
- **Settings tab** — dedicated settings page in the nav bar (Generate / Library / Voices / Settings)
- **AI Assistant** (optional) — Ollama integration for prompt generation; enable/disable via Settings
- **AI auto-naming** — after each generation, AI suggests a short filename (up to 5 words)
- **Toggle switches** — animated on/off toggles for Denoiser and AI settings
- **Model caching** — VoxCPM2 loads in the background at startup and stays in memory; no reload delay between generations
- **GPU acceleration** — CUDA used automatically when available, falls back to CPU
- **Windows executable** — standalone `.exe` built with PyInstaller; no Python install required to run
