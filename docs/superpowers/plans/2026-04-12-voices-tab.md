# Voices Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third "Voices" nav tab with a voice management panel — import, rename, delete, and audition voice files stored in the `audio/` folder.

**Architecture:** A new `src/voices.py` data module (mirrors `library.py`) manages `audio/voices.json`. A new `src/widgets/voices_panel.py` holds `VoiceEntryWidget` and `VoicesPanel`. `NavBar` gets a third button. `app.py` wires everything together.

**Tech Stack:** PyQt6, Python `shutil` + `uuid` for file import, pytest

---

## File Map

| File | Change |
|------|--------|
| `src/voices.py` | New — data module (`load`, `save`, `add_voice`, `rename_voice`, `delete_voice`) |
| `src/widgets/voices_panel.py` | New — `VoiceEntryWidget` + `VoicesPanel` |
| `src/widgets/nav_bar.py` | Add third "Voices" button |
| `src/assets/style.qss` | Add `voicesToolbar` rule |
| `src/app.py` | Import and wire `VoicesPanel` |
| `tests/test_voices.py` | New — tests for `voices.py` CRUD |

---

## Task 1: voices.py data module (TDD)

**Files:**
- Create: `src/voices.py`
- Create: `tests/test_voices.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_voices.py`:

```python
import pytest


@pytest.fixture
def tmp_voices(tmp_path, monkeypatch):
    import src.voices as voices_mod
    monkeypatch.setattr(voices_mod, "VOICES_PATH", tmp_path / "audio" / "voices.json")
    monkeypatch.setattr(voices_mod, "VOICES_DIR", tmp_path / "audio")
    return tmp_path / "audio" / "voices.json"


def test_load_returns_empty_when_no_file(tmp_voices):
    import src.voices as voices_mod
    assert voices_mod.load() == []


def test_load_returns_empty_on_corrupted_file(tmp_voices):
    import src.voices as voices_mod
    tmp_voices.parent.mkdir(parents=True, exist_ok=True)
    tmp_voices.write_bytes(b"not json{{")
    assert voices_mod.load() == []


def test_add_voice_prepends(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.add_voice({"id": "b", "filename": "b.wav", "display_name": "Bob"})
    entries = voices_mod.load()
    assert entries[0]["id"] == "b"
    assert entries[1]["id"] == "a"


def test_rename_voice(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.rename_voice("a", "Alicia")
    assert voices_mod.load()[0]["display_name"] == "Alicia"


def test_rename_unknown_id_is_noop(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.rename_voice("does-not-exist", "Bob")
    assert voices_mod.load()[0]["display_name"] == "Alice"


def test_delete_voice(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.add_voice({"id": "b", "filename": "b.wav", "display_name": "Bob"})
    voices_mod.delete_voice("a")
    entries = voices_mod.load()
    assert len(entries) == 1
    assert entries[0]["id"] == "b"


def test_delete_unknown_id_is_noop(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.delete_voice("does-not-exist")
    assert len(voices_mod.load()) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_voices.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.voices'`

- [ ] **Step 3: Create src/voices.py**

```python
import json
from pathlib import Path

VOICES_DIR = Path(__file__).parent.parent / "audio"
VOICES_PATH = VOICES_DIR / "voices.json"


def load() -> list[dict]:
    if not VOICES_PATH.exists():
        return []
    try:
        with open(VOICES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save(entries: list[dict]) -> None:
    VOICES_PATH.parent.mkdir(exist_ok=True)
    with open(VOICES_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_voice(entry: dict) -> list[dict]:
    entries = load()
    entries.insert(0, entry)
    save(entries)
    return entries


def rename_voice(voice_id: str, display_name: str) -> list[dict]:
    entries = load()
    for e in entries:
        if e["id"] == voice_id:
            e["display_name"] = display_name
            break
    save(entries)
    return entries


def delete_voice(voice_id: str) -> list[dict]:
    entries = [e for e in load() if e["id"] != voice_id]
    save(entries)
    return entries
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_voices.py -v
```

Expected: 7 tests PASS

- [ ] **Step 5: Run full suite to check for regressions**

```bash
pytest tests/ -q
```

Expected: all 47 tests pass (40 existing + 7 new)

- [ ] **Step 6: Commit**

```bash
git add src/voices.py tests/test_voices.py
git commit -m "feat: add voices data module with CRUD functions"
```

---

## Task 2: QSS voicesToolbar rule

**Files:**
- Modify: `src/assets/style.qss` (append after the `libraryPlayingIndicator` block at the end)

- [ ] **Step 1: Append the new rule**

Add this block at the very end of `src/assets/style.qss`:

```css
/* --- Voices toolbar --------------------------------------- */
QWidget#voicesToolbar {
    border-bottom: 1px solid #2a2f3a;
    padding-bottom: 6px;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/assets/style.qss
git commit -m "style: add voicesToolbar rule"
```

---

## Task 3: NavBar — add Voices button

**Files:**
- Modify: `src/widgets/nav_bar.py`

The current file is 33 lines. Replace it entirely with:

```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavBar(QWidget):
    view_changed = pyqtSignal(int)  # 0 = Generate, 1 = Library, 2 = Voices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 0)

        self._generate_btn = QPushButton("Generate")
        self._library_btn = QPushButton("Library")
        self._voices_btn = QPushButton("Voices")

        for btn in (self._generate_btn, self._library_btn, self._voices_btn):
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            layout.addWidget(btn)

        self._generate_btn.setChecked(True)
        layout.addStretch()

        self._generate_btn.clicked.connect(lambda: self._select(0))
        self._library_btn.clicked.connect(lambda: self._select(1))
        self._voices_btn.clicked.connect(lambda: self._select(2))

    def _select(self, index: int) -> None:
        self._generate_btn.setChecked(index == 0)
        self._library_btn.setChecked(index == 1)
        self._voices_btn.setChecked(index == 2)
        self.view_changed.emit(index)
```

- [ ] **Step 1: Replace nav_bar.py with the content above**

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -q
```

Expected: all 47 tests pass

- [ ] **Step 3: Commit**

```bash
git add src/widgets/nav_bar.py
git commit -m "feat: add Voices button to nav bar"
```

---

## Task 4: VoicesPanel widget

**Files:**
- Create: `src/widgets/voices_panel.py`

Create the file with this complete content:

```python
import re
import shutil
import uuid
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src import voices
from src.voices import VOICES_DIR


class VoiceEntryWidget(QWidget):
    play_requested = pyqtSignal(str)         # filename
    rename_requested = pyqtSignal(str, str)  # voice_id, new_display_name
    delete_requested = pyqtSignal(str)       # voice_id

    def __init__(self, entry: dict, row_index: int, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._display_name = entry.get("display_name", "")
        self.setObjectName(
            "libraryRowEven" if row_index % 2 == 0 else "libraryRowOdd"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._name_label = QLabel(self._display_name)
        self._name_label.setFixedWidth(180)

        self._name_edit = QLineEdit(self._display_name)
        self._name_edit.setFixedWidth(180)
        self._name_edit.setVisible(False)
        self._name_edit.editingFinished.connect(self._on_rename_finished)

        filename = entry.get("filename", "")
        file_label = QLabel(filename)
        file_label.setFixedWidth(160)

        suffix = Path(filename).suffix.lstrip(".").upper()
        format_label = QLabel(suffix)
        format_label.setFixedWidth(50)

        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.clicked.connect(lambda: self.play_requested.emit(filename))

        rename_btn = QPushButton("✎")
        rename_btn.setFixedWidth(32)
        rename_btn.clicked.connect(self._start_rename)

        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(32)
        delete_btn.clicked.connect(self._on_delete)

        layout.addWidget(self._name_label)
        layout.addWidget(self._name_edit)
        layout.addWidget(file_label)
        layout.addWidget(format_label)
        layout.addStretch()
        layout.addWidget(play_btn)
        layout.addWidget(rename_btn)
        layout.addWidget(delete_btn)

    def _start_rename(self) -> None:
        self._name_edit.blockSignals(True)
        self._name_edit.setText(self._display_name)
        self._name_edit.blockSignals(False)
        self._name_label.setVisible(False)
        self._name_edit.setVisible(True)
        self._name_edit.setFocus()
        self._name_edit.selectAll()

    def _on_rename_finished(self) -> None:
        new_name = self._name_edit.text().strip()
        self._name_edit.setVisible(False)
        self._name_label.setVisible(True)
        if new_name and new_name != self._display_name:
            self._display_name = new_name
            self._name_label.setText(new_name)
            self.rename_requested.emit(self._entry["id"], new_name)

    def _on_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete {self._display_name!r}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self._entry["id"])


class VoicesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[dict] = []
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("voicesToolbar")
        toolbar_row = QHBoxLayout(toolbar)
        toolbar_row.setContentsMargins(0, 0, 0, 6)
        add_btn = QPushButton("Add Voice")
        toolbar_row.addWidget(add_btn)
        toolbar_row.addStretch()
        layout.addWidget(toolbar)

        # Header row
        header = QWidget()
        header.setObjectName("libraryHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        for col_text, fixed_w in [("Name", 180), ("File", 160), ("Format", 50)]:
            lbl = QLabel(f"<b>{col_text}</b>")
            lbl.setFixedWidth(fixed_w)
            header_layout.addWidget(lbl)
        header_layout.addStretch()
        # 3 buttons × 32px + 2 gaps × ~6px + 4px right margin ≈ 112px
        header_layout.addSpacing(112)
        layout.addWidget(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)

        add_btn.clicked.connect(self._on_add_voice)

    def load_voices(self, entries: list[dict]) -> None:
        self._all_entries = entries
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, entry in enumerate(self._all_entries):
            widget = VoiceEntryWidget(entry, i)
            widget.play_requested.connect(self._on_play_requested)
            widget.rename_requested.connect(self._on_rename_requested)
            widget.delete_requested.connect(self._on_delete_requested)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, widget
            )

    def _on_add_voice(self) -> None:
        src_path, _ = QFileDialog.getOpenFileName(
            self, "Import Voice", "", "Audio Files (*.wav *.mp3)"
        )
        if not src_path:
            return

        src = Path(src_path)
        VOICES_DIR.mkdir(exist_ok=True)

        safe_stem = re.sub(r'[<>:"/\\|?*]', "", src.stem).strip() or "voice"
        dest = VOICES_DIR / f"{safe_stem}{src.suffix.lower()}"
        counter = 2
        while dest.exists():
            dest = VOICES_DIR / f"{safe_stem}_{counter}{src.suffix.lower()}"
            counter += 1

        shutil.copy2(src_path, str(dest))

        display_name, ok = QInputDialog.getText(
            self, "Voice Name", "Display name:", text=src.stem
        )
        if not ok or not display_name.strip():
            dest.unlink()
            return

        entry = {
            "id": uuid.uuid4().hex[:8],
            "filename": dest.name,
            "display_name": display_name.strip(),
        }
        entries = voices.add_voice(entry)
        self.load_voices(entries)

    def _on_play_requested(self, filename: str) -> None:
        path = str(VOICES_DIR / filename)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def _on_rename_requested(self, voice_id: str, new_name: str) -> None:
        # Widget already updated its own label; just persist to disk
        self._all_entries = voices.rename_voice(voice_id, new_name)

    def _on_delete_requested(self, voice_id: str) -> None:
        entry = next((e for e in self._all_entries if e["id"] == voice_id), None)
        if entry:
            file_path = VOICES_DIR / entry["filename"]
            if file_path.exists():
                file_path.unlink()
        entries = voices.delete_voice(voice_id)
        self.load_voices(entries)
```

**Note on `pyqtSignal` placement:** Move the signal declarations outside the class-level import. The `from PyQt6.QtCore import pyqtSignal` import belongs at the top of the file, not inside the class body. Use this corrected imports block at the top of the file:

```python
import re
import shutil
import uuid
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src import voices
from src.voices import VOICES_DIR
```

And the class body for `VoiceEntryWidget` signals (no inline import):

```python
class VoiceEntryWidget(QWidget):
    play_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)
```

- [ ] **Step 1: Create `src/widgets/voices_panel.py` with the content above**

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -q
```

Expected: all 47 tests pass (the widget file is not directly tested — widget tests require a running QApplication)

- [ ] **Step 3: Commit**

```bash
git add src/widgets/voices_panel.py
git commit -m "feat: add VoiceEntryWidget and VoicesPanel"
```

---

## Task 5: Wire app.py

**Files:**
- Modify: `src/app.py`

Two changes needed:

**Change 1:** Add imports. Find the existing import block:

```python
from src import audio, config, library
```

Replace with:

```python
from src import audio, config, library, voices
```

And add the VoicesPanel import after the LibraryPanel import:

```python
from src.widgets.library_panel import LibraryPanel
```

Becomes:

```python
from src.widgets.library_panel import LibraryPanel
from src.widgets.voices_panel import VoicesPanel
```

**Change 2:** In `_setup_ui`, find the Library page block:

```python
        # Page 1: Library view
        self._library_panel = LibraryPanel()
        self._library_panel.load_entries(library.load())
        self._stack.addWidget(self._library_panel)
```

Add the Voices page directly after:

```python
        # Page 2: Voices view
        self._voices_panel = VoicesPanel()
        self._voices_panel.load_voices(voices.load())
        self._stack.addWidget(self._voices_panel)
```

- [ ] **Step 1: Make the two changes to `src/app.py`**

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -q
```

Expected: all 47 tests pass

- [ ] **Step 3: Run the app and verify manually**

```bash
python main.py
```

Check:
- Three tabs visible: Generate / Library / Voices
- Clicking Voices shows the panel with a toolbar ("Add Voice" button) and empty list
- Clicking "Add Voice" opens a file dialog for .wav/.mp3
- After import: file appears in the list with display name, filename, format badge
- ▶ plays audio
- ✎ turns the name into an inline editable field; Enter confirms and updates the display
- ✕ shows confirmation dialog; on Yes, row removed and file deleted from `audio/`
- Switching tabs works correctly; Generate and Library still function

- [ ] **Step 4: Commit**

```bash
git add src/app.py
git commit -m "feat: wire VoicesPanel into app as tab 3"
```

---

## Done

All five tasks complete. The Voices tab is fully functional:
- `src/voices.py` — data module with 7 tested CRUD functions
- `src/widgets/voices_panel.py` — `VoiceEntryWidget` + `VoicesPanel`
- Nav bar has a third tab
- Import copies files to `audio/`, prompts for display name, persists to `voices.json`
- Inline rename, delete with confirmation, audio playback all wired
