# Voice Selector & Button Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix barely-visible icon buttons (▶/✎/✕) in both panels, and replace the Reference Audio section on the Generate tab with a Voice dropdown backed by voices.json.

**Architecture:** A new `VoiceSelector` widget owns a QComboBox populated from `voices.json`. `VoicesPanel` gains a `voices_changed` signal so the dropdown stays in sync when voices are added/deleted/renamed. `config.py` drops the recents concept and tracks `last_voice_id` instead. `ReferencePanel` is deleted.

**Tech Stack:** PyQt6, pytest

---

## File Map

| File | Change |
|------|--------|
| `src/widgets/voices_panel.py` | Add `voices_changed` signal + emit calls + `iconBtn` objectNames |
| `src/widgets/library_panel.py` | Add `iconBtn` objectName to play button |
| `src/assets/style.qss` | Add `QPushButton#iconBtn` rule |
| `src/widgets/voice_selector.py` | New — `VoiceSelector` widget |
| `src/widgets/reference_panel.py` | Deleted |
| `src/app.py` | Replace `_ref_panel` with `_voice_selector`, update handlers |
| `src/config.py` | Remove `last_reference`/`recent_references`/`add_recent_reference`, add `last_voice_id` |
| `tests/test_config.py` | Remove 3 recents tests, update 2 defaults tests |

---

## Task 1: Button visibility fix

**Files:**
- Modify: `src/widgets/voices_panel.py`
- Modify: `src/widgets/library_panel.py`
- Modify: `src/assets/style.qss`

The 32px icon buttons are nearly invisible because `QPushButton { padding: 5px 14px }` leaves ~4px for content. Fix: name the buttons and add a tight-padding rule.

- [ ] **Step 1: Add `setObjectName("iconBtn")` to all three buttons in VoiceEntryWidget**

In `src/widgets/voices_panel.py`, find these three lines (around line 57–66):

```python
        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.clicked.connect(lambda: self.play_requested.emit(filename))

        rename_btn = QPushButton("✎")
        rename_btn.setFixedWidth(32)
        rename_btn.clicked.connect(self._start_rename)

        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(32)
        delete_btn.clicked.connect(self._on_delete)
```

Replace with:

```python
        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.setObjectName("iconBtn")
        play_btn.clicked.connect(lambda: self.play_requested.emit(filename))

        rename_btn = QPushButton("✎")
        rename_btn.setFixedWidth(32)
        rename_btn.setObjectName("iconBtn")
        rename_btn.clicked.connect(self._start_rename)

        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(32)
        delete_btn.setObjectName("iconBtn")
        delete_btn.clicked.connect(self._on_delete)
```

- [ ] **Step 2: Add `setObjectName("iconBtn")` to the play button in LibraryEntryWidget**

In `src/widgets/library_panel.py`, find (around line 78–81):

```python
        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.clicked.connect(
            lambda: self.play_requested.emit(entry.get("filename", ""))
        )
```

Replace with:

```python
        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.setObjectName("iconBtn")
        play_btn.clicked.connect(
            lambda: self.play_requested.emit(entry.get("filename", ""))
        )
```

- [ ] **Step 3: Add the `iconBtn` QSS rule**

In `src/assets/style.qss`, append at the very end (after the `voicesToolbar` block):

```css
/* --- Small icon buttons ----------------------------------- */
QPushButton#iconBtn {
    padding: 2px 0px;
    font-size: 13px;
}
```

- [ ] **Step 4: Run full test suite to verify no regressions**

```bash
pytest tests/ -q
```

Expected: 47 passed

- [ ] **Step 5: Commit**

```bash
git add src/widgets/voices_panel.py src/widgets/library_panel.py src/assets/style.qss
git commit -m "fix: make icon buttons visible with tight-padding QSS rule"
```

---

## Task 2: config.py — remove recents, add last_voice_id (TDD)

**Files:**
- Modify: `src/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write the updated test file**

Replace the entire contents of `tests/test_config.py` with:

```python
import json
import pytest


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
    assert result["last_voice_id"] == ""


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


def test_load_returns_defaults_on_corrupted_file(tmp_config):
    import src.config as cfg_mod
    tmp_config.write_bytes(b"not valid json{{{{")
    result = cfg_mod.load()
    assert result["cfg_value"] == 2.0
    assert result["last_voice_id"] == ""


def test_load_includes_ollama_defaults(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["ollama_enabled"] is False
    assert result["ollama_host"] == "127.0.0.1"
    assert result["ollama_port"] == 11434
    assert result["ollama_model"] == ""


def test_load_includes_voice_profiles_default(tmp_config):
    import src.config as cfg_mod
    result = cfg_mod.load()
    assert result["voice_profiles"] == {}
```

- [ ] **Step 2: Run to verify failures**

```bash
pytest tests/test_config.py -v
```

Expected: `test_load_defaults_when_no_file` FAILS (KeyError on `last_voice_id`), `test_load_returns_defaults_on_corrupted_file` FAILS. Other tests may pass. 3 add_recent_reference tests are gone (no longer collected).

- [ ] **Step 3: Update config.py**

Replace the entire contents of `src/config.py` with:

```python
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULTS = {
    "last_voice_id": "",
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "use_denoiser": False,
    "ollama_enabled": False,
    "ollama_host": "127.0.0.1",
    "ollama_port": 11434,
    "ollama_model": "",
    "voice_profiles": {},
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()
    return {**DEFAULTS, **data}


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
```

- [ ] **Step 4: Run to verify all pass**

```bash
pytest tests/test_config.py -v
```

Expected: 6 passed

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -q
```

Expected: 44 passed (47 − 3 removed recents tests)

- [ ] **Step 6: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: replace last_reference/recents with last_voice_id in config"
```

---

## Task 3: VoiceSelector widget

**Files:**
- Create: `src/widgets/voice_selector.py`

- [ ] **Step 1: Create `src/widgets/voice_selector.py`**

```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from src.voices import VOICES_DIR


class VoiceSelector(QWidget):
    voice_changed = pyqtSignal(str, str)  # voice_id, absolute_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Voice:")
        label.setFixedWidth(50)

        self._combo = QComboBox()
        self._combo.setPlaceholderText("No voices — import one in the Voices tab")
        self._combo.setEnabled(False)

        layout.addWidget(label)
        layout.addWidget(self._combo, stretch=1)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

    def refresh(self, entries: list[dict]) -> None:
        """Repopulate the combo. Restores previous selection by voice ID if still
        present; otherwise falls back to index 0. Emits voice_changed if the
        active voice ID changed (e.g. after a deletion forced a fallback)."""
        old_id = self.current_voice_id()
        self._entries = entries
        self._combo.blockSignals(True)
        self._combo.clear()
        for entry in entries:
            self._combo.addItem(entry["display_name"])
        if entries:
            idx = next(
                (i for i, e in enumerate(entries) if e["id"] == old_id), 0
            )
            self._combo.setCurrentIndex(idx)
        self._combo.setEnabled(bool(entries))
        self._combo.blockSignals(False)
        new_id = self.current_voice_id()
        if new_id is not None and new_id != old_id:
            e = entries[self._combo.currentIndex()]
            self.voice_changed.emit(e["id"], str(VOICES_DIR / e["filename"]))

    def select_by_id(self, voice_id: str) -> None:
        """Select a specific voice by ID. Triggers voice_changed if the index
        changes. Used once at startup to restore last_voice_id from config."""
        idx = next(
            (i for i, e in enumerate(self._entries) if e["id"] == voice_id), None
        )
        if idx is not None:
            self._combo.setCurrentIndex(idx)

    def current_voice_id(self) -> str | None:
        idx = self._combo.currentIndex()
        if idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]["id"]

    def current_path(self) -> str | None:
        idx = self._combo.currentIndex()
        if idx < 0 or idx >= len(self._entries):
            return None
        return str(VOICES_DIR / self._entries[idx]["filename"])

    def _on_index_changed(self, idx: int) -> None:
        if 0 <= idx < len(self._entries):
            e = self._entries[idx]
            self.voice_changed.emit(e["id"], str(VOICES_DIR / e["filename"]))
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -q
```

Expected: 44 passed

- [ ] **Step 3: Commit**

```bash
git add src/widgets/voice_selector.py
git commit -m "feat: add VoiceSelector widget with combo backed by voices.json"
```

---

## Task 4: VoicesPanel — voices_changed signal

**Files:**
- Modify: `src/widgets/voices_panel.py`

`VoicesPanel` currently handles mutations silently. The Generate tab's `VoiceSelector` needs to know when voices change. Add a `voices_changed = pyqtSignal(list)` and emit it after every mutation.

- [ ] **Step 1: Add the signal declaration**

In `src/widgets/voices_panel.py`, find:

```python
class VoicesPanel(QWidget):
    def __init__(self, parent=None):
```

Replace with:

```python
class VoicesPanel(QWidget):
    voices_changed = pyqtSignal(list)  # emits updated entries list after any mutation

    def __init__(self, parent=None):
```

- [ ] **Step 2: Emit after add**

Find `_on_add_voice`, the last two lines:

```python
        entries = voices.add_voice(entry)
        self.load_voices(entries)
```

Replace with:

```python
        entries = voices.add_voice(entry)
        self.load_voices(entries)
        self.voices_changed.emit(entries)
```

- [ ] **Step 3: Emit after rename**

Find `_on_rename_requested`:

```python
    def _on_rename_requested(self, voice_id: str, new_name: str) -> None:
        # Widget already updated its own label; just persist to disk
        self._all_entries = voices.rename_voice(voice_id, new_name)
```

Replace with:

```python
    def _on_rename_requested(self, voice_id: str, new_name: str) -> None:
        # Widget already updated its own label; just persist to disk
        self._all_entries = voices.rename_voice(voice_id, new_name)
        self.voices_changed.emit(self._all_entries)
```

- [ ] **Step 4: Emit after delete**

Find `_on_delete_requested`, the last two lines:

```python
        entries = voices.delete_voice(voice_id)
        self.load_voices(entries)
```

Replace with:

```python
        entries = voices.delete_voice(voice_id)
        self.load_voices(entries)
        self.voices_changed.emit(entries)
```

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -q
```

Expected: 44 passed

- [ ] **Step 6: Commit**

```bash
git add src/widgets/voices_panel.py
git commit -m "feat: emit voices_changed signal after every VoicesPanel mutation"
```

---

## Task 5: Wire app.py + delete ReferencePanel

**Files:**
- Modify: `src/app.py`
- Delete: `src/widgets/reference_panel.py`

- [ ] **Step 1: Update imports in app.py**

Find:

```python
from src import audio, config, library
```

Replace with:

```python
from src import audio, config, library, voices
```

Find:

```python
from src.widgets.reference_panel import ReferencePanel
```

Replace with:

```python
from src.widgets.voice_selector import VoiceSelector
```

- [ ] **Step 2: Replace ReferencePanel construction in `_setup_ui`**

Find:

```python
        self._ref_panel = ReferencePanel(self._cfg)
        self._ai_panel = AIPanel(
```

Replace with:

```python
        self._voice_selector = VoiceSelector()
        self._voice_selector.refresh(voices.load())
        if self._cfg.get("last_voice_id"):
            self._voice_selector.select_by_id(self._cfg["last_voice_id"])
        self._ai_panel = AIPanel(
```

Find:

```python
        gen_layout.addWidget(self._ref_panel)
```

Replace with:

```python
        gen_layout.addWidget(self._voice_selector)
```

- [ ] **Step 3: Update signal connections in `_setup_ui`**

Find:

```python
        self._ref_panel.reference_changed.connect(self._on_reference_changed)
```

Replace with:

```python
        self._voice_selector.voice_changed.connect(self._on_voice_changed)
        self._voices_panel.voices_changed.connect(self._voice_selector.refresh)
```

- [ ] **Step 4: Replace `_on_reference_changed` with `_on_voice_changed`**

Find and delete the entire `_on_reference_changed` method:

```python
    def _on_reference_changed(self, path: str):
        self._cfg = config.add_recent_reference(self._cfg, path)
        config.save(self._cfg)
        self._ref_panel.update_recents(self._cfg)

        profile = self._cfg["voice_profiles"].get(path)
        if profile:
            self._settings_panel.set_values(
                profile["cfg_value"],
                profile["inference_timesteps"],
                profile["use_denoiser"],
            )
        else:
            self._settings_panel.set_values(2.0, 10, False)
```

Add the new method in its place:

```python
    def _on_voice_changed(self, voice_id: str, path: str) -> None:
        self._cfg["last_voice_id"] = voice_id
        config.save(self._cfg)
        profile = self._cfg["voice_profiles"].get(voice_id)
        if profile:
            self._settings_panel.set_values(
                profile["cfg_value"],
                profile["inference_timesteps"],
                profile["use_denoiser"],
            )
        else:
            self._settings_panel.set_values(2.0, 10, False)
```

- [ ] **Step 5: Update `_on_settings_changed`**

Find:

```python
    def _on_settings_changed(self, values: dict):
        self._cfg.update(values)
        current_voice = self._ref_panel.current_path()
        if current_voice:
            self._cfg["voice_profiles"][current_voice] = {
                "cfg_value": values["cfg_value"],
                "inference_timesteps": values["inference_timesteps"],
                "use_denoiser": values["use_denoiser"],
            }
        config.save(self._cfg)
```

Replace with:

```python
    def _on_settings_changed(self, values: dict):
        self._cfg.update(values)
        current_voice_id = self._voice_selector.current_voice_id()
        if current_voice_id:
            self._cfg["voice_profiles"][current_voice_id] = {
                "cfg_value": values["cfg_value"],
                "inference_timesteps": values["inference_timesteps"],
                "use_denoiser": values["use_denoiser"],
            }
        config.save(self._cfg)
```

- [ ] **Step 6: Update `_on_generate`**

Find:

```python
        ref_path = self._ref_panel.current_path()
        text = self._text_panel.text()

        if not ref_path:
            self._output_panel.show_warning("Please select a reference audio file.")
```

Replace with:

```python
        ref_path = self._voice_selector.current_path()
        text = self._text_panel.text()

        if not ref_path:
            self._output_panel.show_warning("Please select a voice.")
```

- [ ] **Step 7: Update `_on_generation_done`**

Find:

```python
        ref_path = self._ref_panel.current_path()
```

Replace with:

```python
        ref_path = self._voice_selector.current_path()
```

- [ ] **Step 8: Delete reference_panel.py**

```bash
git rm src/widgets/reference_panel.py
```

- [ ] **Step 9: Run full test suite**

```bash
pytest tests/ -q
```

Expected: 44 passed

- [ ] **Step 10: Commit**

```bash
git add src/app.py
git commit -m "feat: replace ReferencePanel with VoiceSelector on Generate tab"
```

---

## Done

All five tasks complete:
- 32px icon buttons are visible in both panels
- `config.py` tracks `last_voice_id`, no more recents
- `VoiceSelector` dropdown backed by `voices.json`, per-voice settings preserved
- `VoicesPanel` notifies the dropdown on every mutation
- `ReferencePanel` deleted
