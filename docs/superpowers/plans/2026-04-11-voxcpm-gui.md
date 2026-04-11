# VoxCPM GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PyQt6 desktop GUI for VoxCPM2 voice cloning — select reference audio, enter text, tweak parameters, generate and play back cloned-voice audio.

**Architecture:** Package structure under `src/` with four widget panels (reference, text, settings, output) wired together by a `MainWindow` in `app.py`. Generation runs in a `QThread` worker so the UI stays responsive. Persistent settings stored in `config.json` at the project root.

**Tech Stack:** PyQt6, PyQt6-Qt6 (QtMultimedia), voxcpm, soundfile, imageio_ffmpeg, pytest

---

## File Map

| Path | Responsibility |
|---|---|
| `main.py` | Entry point — creates `QApplication`, launches `MainWindow` |
| `src/__init__.py` | Package marker |
| `src/app.py` | `MainWindow` — assembles panels, wires signals/slots |
| `src/config.py` | Load/save `config.json`, manage recent references |
| `src/audio.py` | mp3→wav conversion, timestamped output path |
| `src/model.py` | `GenerationWorker(QThread)` — wraps VoxCPM generate call |
| `src/widgets/__init__.py` | Package marker |
| `src/widgets/reference_panel.py` | File picker + recent references list |
| `src/widgets/text_panel.py` | Multiline text input |
| `src/widgets/settings_panel.py` | Linked sliders/spinboxes for cfg_value, steps; denoiser checkbox |
| `src/widgets/output_panel.py` | Generate button, progress bar, playback controls, output path label |
| `tests/__init__.py` | Package marker |
| `tests/test_config.py` | Unit tests for config load/save/recents logic |
| `tests/test_audio.py` | Unit tests for output_path and ensure_wav |

---

## Task 1: Install PyQt6 and scaffold the package

**Files:**
- Create: `src/__init__.py`
- Create: `src/widgets/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Install PyQt6**

```bash
pip install PyQt6
```

Expected output includes: `Successfully installed PyQt6-...`

- [ ] **Step 2: Verify QtMultimedia is available**

```bash
python -c "from PyQt6.QtMultimedia import QMediaPlayer; print('ok')"
```

Expected: `ok`  
If this fails, run: `pip install PyQt6-Qt6` and retry.

- [ ] **Step 3: Create package markers**

Create `src/__init__.py` (empty file):
```python
```

Create `src/widgets/__init__.py` (empty file):
```python
```

Create `tests/__init__.py` (empty file):
```python
```

- [ ] **Step 4: Delete old scripts**

```bash
rm E:/Coding/VoxCPM/borat.py E:/Coding/VoxCPM/optimus.py
```

- [ ] **Step 5: Commit**

```bash
cd E:/Coding/VoxCPM
git add src/ tests/
git commit -m "chore: scaffold package structure, remove old scripts"
```

---

## Task 2: config.py

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:
```python
import json
import os
import pytest
from pathlib import Path


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Patch CONFIG_PATH to a temp file."""
    import src.config as cfg_mod
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", tmp_path / "config.json")
    return tmp_path / "config.json"


def test_load_defaults_when_no_file(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["cfg_value"] == 2.0
    assert result["inference_timesteps"] == 10
    assert result["use_denoiser"] is False
    assert result["last_reference"] == ""
    assert result["recent_references"] == []


def test_load_merges_with_defaults(tmp_config):
    import src.config as cfg_mod
    tmp_config.write_text(json.dumps({"cfg_value": 5.0}))
    result = cfg_mod.load()
    assert result["cfg_value"] == 5.0
    assert result["inference_timesteps"] == 10  # default still present


def test_save_and_reload(tmp_config):
    import src.config as cfg_mod
    cfg = cfg_mod.load()
    cfg["cfg_value"] = 3.5
    cfg_mod.save(cfg)
    reloaded = cfg_mod.load()
    assert reloaded["cfg_value"] == 3.5


def test_add_recent_reference_prepends(tmp_config):
    import src.config as cfg_mod
    cfg = cfg_mod.load()
    cfg = cfg_mod.add_recent_reference(cfg, "/audio/a.wav")
    cfg = cfg_mod.add_recent_reference(cfg, "/audio/b.wav")
    assert cfg["recent_references"][0] == "/audio/b.wav"
    assert cfg["recent_references"][1] == "/audio/a.wav"
    assert cfg["last_reference"] == "/audio/b.wav"


def test_add_recent_reference_deduplicates(tmp_config):
    import src.config as cfg_mod
    cfg = cfg_mod.load()
    cfg = cfg_mod.add_recent_reference(cfg, "/audio/a.wav")
    cfg = cfg_mod.add_recent_reference(cfg, "/audio/a.wav")
    assert cfg["recent_references"].count("/audio/a.wav") == 1


def test_add_recent_reference_caps_at_10(tmp_config):
    import src.config as cfg_mod
    cfg = cfg_mod.load()
    for i in range(12):
        cfg = cfg_mod.add_recent_reference(cfg, f"/audio/{i}.wav")
    assert len(cfg["recent_references"]) == 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd E:/Coding/VoxCPM
pytest tests/test_config.py -v
```

Expected: all 6 tests FAIL with `ModuleNotFoundError` or `AttributeError`.

- [ ] **Step 3: Implement config.py**

Create `src/config.py`:
```python
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULTS = {
    "last_reference": "",
    "recent_references": [],
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "use_denoiser": False,
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    return {**DEFAULTS, **data}


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def add_recent_reference(cfg: dict, path: str) -> dict:
    recents = [p for p in cfg["recent_references"] if p != path]
    recents.insert(0, path)
    cfg = dict(cfg)
    cfg["recent_references"] = recents[:10]
    cfg["last_reference"] = path
    return cfg
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add config load/save with persistent recent references"
```

---

## Task 3: audio.py

**Files:**
- Create: `src/audio.py`
- Create: `tests/test_audio.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_audio.py`:
```python
import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def tmp_output(tmp_path, monkeypatch):
    import src.audio as audio_mod
    monkeypatch.setattr(audio_mod, "OUTPUT_DIR", tmp_path / "output")
    return tmp_path / "output"


def test_output_path_creates_directory(tmp_output):
    import src.audio as audio_mod
    path = audio_mod.output_path()
    assert tmp_output.exists()


def test_output_path_format(tmp_output):
    import src.audio as audio_mod
    path = audio_mod.output_path()
    filename = Path(path).name
    assert re.match(r"\d{4}-\d{2}-\d{2}_\d{6}\.wav", filename), f"Bad format: {filename}"


def test_ensure_wav_passthrough_for_wav(tmp_path):
    import src.audio as audio_mod
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"")
    result = audio_mod.ensure_wav(str(wav_file))
    assert result == str(wav_file)


def test_ensure_wav_converts_mp3(tmp_path):
    import src.audio as audio_mod
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"fake mp3")
    wav_expected = tmp_path / "test.wav"

    with patch("src.audio.subprocess.run") as mock_run, \
         patch("src.audio.imageio_ffmpeg.get_ffmpeg_exe", return_value="/usr/bin/ffmpeg"):
        mock_run.return_value = MagicMock(returncode=0)
        result = audio_mod.ensure_wav(str(mp3_file))

    assert result == str(wav_expected)
    mock_run.assert_called_once()


def test_ensure_wav_skips_conversion_if_wav_exists(tmp_path):
    import src.audio as audio_mod
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"fake mp3")
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"existing wav")

    with patch("src.audio.subprocess.run") as mock_run:
        result = audio_mod.ensure_wav(str(mp3_file))

    mock_run.assert_not_called()
    assert result == str(wav_file)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_audio.py -v
```

Expected: all 5 tests FAIL.

- [ ] **Step 3: Implement audio.py**

Create `src/audio.py`:
```python
import subprocess
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def ensure_wav(path: str) -> str:
    """Return a .wav path for the given audio file, converting from mp3 if needed."""
    p = Path(path)
    if p.suffix.lower() == ".wav":
        return str(p)
    wav_path = p.with_suffix(".wav")
    if not wav_path.exists():
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-i", str(p), str(wav_path)], check=True)
    return str(wav_path)


def output_path() -> str:
    """Return a timestamped output path, creating the output directory if needed."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return str(OUTPUT_DIR / f"{timestamp}.wav")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_audio.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/audio.py tests/test_audio.py
git commit -m "feat: add audio conversion and timestamped output path helpers"
```

---

## Task 4: model.py — GenerationWorker

**Files:**
- Create: `src/model.py`

- [ ] **Step 1: Implement model.py**

Create `src/model.py`:
```python
from PyQt6.QtCore import QThread, pyqtSignal


class GenerationWorker(QThread):
    finished = pyqtSignal(object, int)  # (wav ndarray, sample_rate)
    error = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        reference_wav: str,
        cfg_value: float,
        inference_timesteps: int,
        use_denoiser: bool,
    ):
        super().__init__()
        self.text = text
        self.reference_wav = reference_wav
        self.cfg_value = cfg_value
        self.inference_timesteps = inference_timesteps
        self.use_denoiser = use_denoiser

    def run(self):
        try:
            from voxcpm import VoxCPM

            model = VoxCPM.from_pretrained(
                "openbmb/VoxCPM2", load_denoiser=self.use_denoiser
            )
            wav = model.generate(
                text=self.text,
                reference_wav_path=self.reference_wav,
                cfg_value=self.cfg_value,
                inference_timesteps=self.inference_timesteps,
            )
            self.finished.emit(wav, model.tts_model.sample_rate)
        except Exception as e:
            self.error.emit(str(e))
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
python -c "from src.model import GenerationWorker; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/model.py
git commit -m "feat: add GenerationWorker QThread for non-blocking voice generation"
```

---

## Task 5: ReferencePanel widget

**Files:**
- Create: `src/widgets/reference_panel.py`

- [ ] **Step 1: Implement reference_panel.py**

Create `src/widgets/reference_panel.py`:
```python
import os

from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal


class ReferencePanel(QGroupBox):
    reference_changed = pyqtSignal(str)  # emits absolute path

    def __init__(self, cfg: dict, parent=None):
        super().__init__("Reference Audio", parent)
        self._cfg = cfg
        self._current_path = ""
        self._setup_ui()
        if cfg.get("last_reference"):
            self._set_path(cfg["last_reference"])

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        browse_row = QHBoxLayout()
        self._browse_btn = QPushButton("Browse...")
        self._path_label = QLabel("No file selected")
        self._path_label.setWordWrap(True)
        browse_row.addWidget(self._browse_btn)
        browse_row.addWidget(self._path_label, 1)
        layout.addLayout(browse_row)

        self._recents_layout = QHBoxLayout()
        layout.addLayout(self._recents_layout)
        self._refresh_recents()

        self._browse_btn.clicked.connect(self._on_browse)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Audio", "", "Audio Files (*.wav *.mp3)"
        )
        if path:
            self._set_path(path)

    def _set_path(self, path: str):
        self._current_path = path
        self._path_label.setText(path)
        self.reference_changed.emit(path)

    def _refresh_recents(self):
        while self._recents_layout.count():
            item = self._recents_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for path in self._cfg.get("recent_references", []):
            name = os.path.basename(path)
            btn = QPushButton(name)
            btn.setFlat(True)
            btn.setToolTip(path)
            btn.clicked.connect(lambda checked, p=path: self._set_path(p))
            self._recents_layout.addWidget(btn)

        self._recents_layout.addStretch()

    def update_recents(self, cfg: dict):
        self._cfg = cfg
        self._refresh_recents()

    def current_path(self) -> str:
        return self._current_path
```

- [ ] **Step 2: Smoke-test that it instantiates**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from src.widgets.reference_panel import ReferencePanel
p = ReferencePanel({})
p.show()
print('ReferencePanel ok')
app.quit()
"
```

Expected: `ReferencePanel ok`

- [ ] **Step 3: Commit**

```bash
git add src/widgets/reference_panel.py
git commit -m "feat: add ReferencePanel with file picker and recent references"
```

---

## Task 6: TextPanel widget

**Files:**
- Create: `src/widgets/text_panel.py`

- [ ] **Step 1: Implement text_panel.py**

Create `src/widgets/text_panel.py`:
```python
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QPlainTextEdit


class TextPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Text to Speak", parent)
        layout = QVBoxLayout(self)
        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText("Enter text to speak...")
        self._text_edit.setMinimumHeight(100)
        layout.addWidget(self._text_edit)

    def text(self) -> str:
        return self._text_edit.toPlainText().strip()
```

- [ ] **Step 2: Smoke-test**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from src.widgets.text_panel import TextPanel
p = TextPanel()
assert p.text() == ''
print('TextPanel ok')
app.quit()
"
```

Expected: `TextPanel ok`

- [ ] **Step 3: Commit**

```bash
git add src/widgets/text_panel.py
git commit -m "feat: add TextPanel for multiline text input"
```

---

## Task 7: SettingsPanel widget

**Files:**
- Create: `src/widgets/settings_panel.py`

- [ ] **Step 1: Implement settings_panel.py**

Create `src/widgets/settings_panel.py`:
```python
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QWidget,
)


class SettingsPanel(QGroupBox):
    settings_changed = pyqtSignal(dict)

    def __init__(self, cfg: dict, parent=None):
        super().__init__("Voice Settings", parent)
        self._setup_ui(cfg)

    def _setup_ui(self, cfg: dict):
        layout = QFormLayout(self)

        # --- CFG Value ---
        cfg_widget = QWidget()
        cfg_row = QHBoxLayout(cfg_widget)
        cfg_row.setContentsMargins(0, 0, 0, 0)
        self._cfg_slider = QSlider(Qt.Orientation.Horizontal)
        self._cfg_slider.setRange(1, 100)  # 1 = 0.1, 100 = 10.0
        self._cfg_spin = QDoubleSpinBox()
        self._cfg_spin.setRange(0.1, 10.0)
        self._cfg_spin.setSingleStep(0.1)
        self._cfg_spin.setDecimals(1)
        self._cfg_spin.setFixedWidth(70)
        cfg_row.addWidget(self._cfg_slider)
        cfg_row.addWidget(self._cfg_spin)
        layout.addRow("CFG Value", cfg_widget)

        # --- Inference Steps ---
        steps_widget = QWidget()
        steps_row = QHBoxLayout(steps_widget)
        steps_row.setContentsMargins(0, 0, 0, 0)
        self._steps_slider = QSlider(Qt.Orientation.Horizontal)
        self._steps_slider.setRange(1, 100)
        self._steps_spin = QSpinBox()
        self._steps_spin.setRange(1, 100)
        self._steps_spin.setFixedWidth(70)
        steps_row.addWidget(self._steps_slider)
        steps_row.addWidget(self._steps_spin)
        layout.addRow("Inference Steps", steps_widget)

        # --- Denoiser ---
        self._denoiser_check = QCheckBox()
        layout.addRow("Use Denoiser", self._denoiser_check)

        # Set initial values (block signals to avoid spurious saves on startup)
        self._cfg_spin.blockSignals(True)
        self._cfg_slider.blockSignals(True)
        self._steps_spin.blockSignals(True)
        self._steps_slider.blockSignals(True)
        self._denoiser_check.blockSignals(True)

        self._cfg_spin.setValue(cfg.get("cfg_value", 2.0))
        self._cfg_slider.setValue(int(round(cfg.get("cfg_value", 2.0) * 10)))
        self._steps_spin.setValue(cfg.get("inference_timesteps", 10))
        self._steps_slider.setValue(cfg.get("inference_timesteps", 10))
        self._denoiser_check.setChecked(cfg.get("use_denoiser", False))

        self._cfg_spin.blockSignals(False)
        self._cfg_slider.blockSignals(False)
        self._steps_spin.blockSignals(False)
        self._steps_slider.blockSignals(False)
        self._denoiser_check.blockSignals(False)

        # Link slider <-> spinbox (bidirectional)
        self._cfg_slider.valueChanged.connect(
            lambda v: self._cfg_spin.setValue(round(v / 10, 1))
        )
        self._cfg_spin.valueChanged.connect(
            lambda v: self._cfg_slider.setValue(int(round(v * 10)))
        )
        self._steps_slider.valueChanged.connect(self._steps_spin.setValue)
        self._steps_spin.valueChanged.connect(self._steps_slider.setValue)

        # Emit settings_changed on any change
        self._cfg_spin.valueChanged.connect(self._emit)
        self._steps_spin.valueChanged.connect(self._emit)
        self._denoiser_check.toggled.connect(self._emit)

    def _emit(self, _=None):
        self.settings_changed.emit(self.values())

    def values(self) -> dict:
        return {
            "cfg_value": self._cfg_spin.value(),
            "inference_timesteps": self._steps_spin.value(),
            "use_denoiser": self._denoiser_check.isChecked(),
        }
```

- [ ] **Step 2: Smoke-test**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from src.widgets.settings_panel import SettingsPanel
p = SettingsPanel({'cfg_value': 2.0, 'inference_timesteps': 10, 'use_denoiser': False})
v = p.values()
assert v['cfg_value'] == 2.0
assert v['inference_timesteps'] == 10
assert v['use_denoiser'] is False
print('SettingsPanel ok')
app.quit()
"
```

Expected: `SettingsPanel ok`

- [ ] **Step 3: Commit**

```bash
git add src/widgets/settings_panel.py
git commit -m "feat: add SettingsPanel with linked sliders and spinboxes"
```

---

## Task 8: OutputPanel widget

**Files:**
- Create: `src/widgets/output_panel.py`

- [ ] **Step 1: Implement output_panel.py**

Create `src/widgets/output_panel.py`:
```python
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class OutputPanel(QGroupBox):
    generate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Output", parent)
        self._last_output: str | None = None
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._setup_ui()
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._generate_btn = QPushButton("Generate")
        self._play_btn = QPushButton("▶ Play")
        self._stop_btn = QPushButton("■ Stop")
        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        btn_row.addWidget(self._generate_btn)
        btn_row.addWidget(self._play_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._generate_btn.clicked.connect(self.generate_requested)
        self._play_btn.clicked.connect(self._play)
        self._stop_btn.clicked.connect(self._stop)

    def set_generating(self, generating: bool):
        self._generate_btn.setEnabled(not generating)
        self._progress.setVisible(generating)
        if generating:
            self._status_label.setText("Generating...")

    def set_output(self, path: str):
        self._last_output = path
        self._status_label.setText(path)
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._play_btn.setEnabled(True)

    def show_error(self, message: str):
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText("Generation failed.")
        QMessageBox.critical(self, "Generation Failed", message)

    def show_warning(self, message: str):
        self._status_label.setText(message)

    def _play(self):
        if self._last_output:
            self._player.setSource(QUrl.fromLocalFile(self._last_output))
            self._player.play()
            self._stop_btn.setEnabled(True)

    def _stop(self):
        self._player.stop()

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._stop_btn.setEnabled(False)
```

- [ ] **Step 2: Smoke-test**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from src.widgets.output_panel import OutputPanel
p = OutputPanel()
p.show_warning('test warning')
print('OutputPanel ok')
app.quit()
"
```

Expected: `OutputPanel ok`

- [ ] **Step 3: Commit**

```bash
git add src/widgets/output_panel.py
git commit -m "feat: add OutputPanel with progress bar and QMediaPlayer playback"
```

---

## Task 9: MainWindow (app.py)

**Files:**
- Create: `src/app.py`

- [ ] **Step 1: Implement app.py**

Create `src/app.py`:
```python
import soundfile as sf
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from src import audio, config
from src.model import GenerationWorker
from src.widgets.output_panel import OutputPanel
from src.widgets.reference_panel import ReferencePanel
from src.widgets.settings_panel import SettingsPanel
from src.widgets.text_panel import TextPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoxCPM Voice Cloner")
        self.setMinimumWidth(620)
        self._cfg = config.load()
        self._worker: GenerationWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        self._ref_panel = ReferencePanel(self._cfg)
        self._text_panel = TextPanel()
        self._settings_panel = SettingsPanel(self._cfg)
        self._output_panel = OutputPanel()

        layout.addWidget(self._ref_panel)
        layout.addWidget(self._text_panel)
        layout.addWidget(self._settings_panel)
        layout.addWidget(self._output_panel)

        self._ref_panel.reference_changed.connect(self._on_reference_changed)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)
        self._output_panel.generate_requested.connect(self._on_generate)

    def _on_reference_changed(self, path: str):
        self._cfg = config.add_recent_reference(self._cfg, path)
        config.save(self._cfg)
        self._ref_panel.update_recents(self._cfg)

    def _on_settings_changed(self, values: dict):
        self._cfg.update(values)
        config.save(self._cfg)

    def _on_generate(self):
        ref_path = self._ref_panel.current_path()
        text = self._text_panel.text()

        if not ref_path:
            self._output_panel.show_warning("Please select a reference audio file.")
            return
        if not text:
            self._output_panel.show_warning("Please enter text to speak.")
            return

        try:
            wav_ref = audio.ensure_wav(ref_path)
        except Exception as e:
            self._output_panel.show_error(f"Failed to convert reference audio:\n{e}")
            return

        self._output_panel.set_generating(True)
        self._worker = GenerationWorker(
            text=text,
            reference_wav=wav_ref,
            cfg_value=self._cfg["cfg_value"],
            inference_timesteps=self._cfg["inference_timesteps"],
            use_denoiser=self._cfg["use_denoiser"],
        )
        self._worker.finished.connect(self._on_generation_done)
        self._worker.error.connect(self._output_panel.show_error)
        self._worker.start()

    def _on_generation_done(self, wav, sample_rate: int):
        out_path = audio.output_path()
        sf.write(out_path, wav, sample_rate)
        self._output_panel.set_output(out_path)
```

- [ ] **Step 2: Smoke-test MainWindow instantiation**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from src.app import MainWindow
w = MainWindow()
w.show()
print('MainWindow ok')
app.quit()
"
```

Expected: `MainWindow ok`

- [ ] **Step 3: Commit**

```bash
git add src/app.py
git commit -m "feat: add MainWindow wiring all panels together"
```

---

## Task 10: Entry point and full run

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

Create `main.py`:
```python
import sys
from PyQt6.QtWidgets import QApplication
from src.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VoxCPM Voice Cloner")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

```bash
cd E:/Coding/VoxCPM
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Launch the app and verify manually**

```bash
python main.py
```

Manual checks:
- [ ] Window opens with all four panels visible
- [ ] Click Browse, select an audio file — path appears in the panel and file appears in the Recent list
- [ ] Close and reopen the app — the reference and slider values are restored from `config.json`
- [ ] Enter some text, click Generate — progress bar appears, Generate button disables
- [ ] After generation: output path appears, Play button enables
- [ ] Click Play — audio plays; Stop button enables while playing, disables when done
- [ ] Try generating with no reference selected — warning label appears, no crash
- [ ] Try generating with empty text — warning label appears, no crash

- [ ] **Step 4: Final commit**

```bash
git add main.py
git commit -m "feat: add entry point, VoxCPM GUI complete"
```
