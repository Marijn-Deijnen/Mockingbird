# Library Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat filter-list library with a file-manager-style table: toolbar (search + voice filter + sort preset), clean data rows with inline play, and a collapsible detail panel at the bottom for rename/delete/metadata.

**Architecture:** `LibraryPanel` is fully rewritten into four vertical zones — toolbar, header, scrollable table, detail panel. `LibraryEntryWidget` loses the delete button and gains selection signals. A new `LibraryDetailPanel` class handles rename, delete, metadata, and playback indicator. Filtering and sorting is extracted into a pure `filter_entries` function for testability.

**Tech Stack:** PyQt6 (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QLabel, QScrollArea, QMediaPlayer, QAudioOutput, QMessageBox, pyqtSignal), pytest

---

## File Map

| File | Change |
|------|--------|
| `src/assets/style.qss` | Add 4 new rules: `libraryToolbar`, `libraryDetail`, `libraryRowSelected`, `libraryPlayingIndicator` |
| `src/widgets/library_panel.py` | Full rewrite: add `filter_entries` function, rewrite `LibraryEntryWidget`, add `LibraryDetailPanel`, rewrite `LibraryPanel` |
| `src/app.py` | Add one signal connection: `self._library_panel.file_renamed.connect(self._on_file_renamed)` |
| `tests/test_library_panel.py` | New file: tests for `filter_entries` pure function |

---

## Task 1: QSS additions

**Files:**
- Modify: `src/assets/style.qss` (append at end of file, after the `/* --- Tooltip ---` block)

- [ ] **Step 1: Append the four new rules to style.qss**

Add this block at the very end of `src/assets/style.qss`:

```css
/* --- Library toolbar -------------------------------------- */
QWidget#libraryToolbar {
    border-bottom: 1px solid #2a2f3a;
    padding-bottom: 6px;
}

/* --- Library detail panel --------------------------------- */
QWidget#libraryDetail {
    border-top: 1px solid #3a4150;
    padding-top: 6px;
}

/* --- Library selected row --------------------------------- */
QWidget#libraryRowSelected {
    background-color: #313848;
    border-radius: 0;
}

/* --- Library playing indicator ---------------------------- */
QLabel#libraryPlayingIndicator {
    color: #e8a838;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10px;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/assets/style.qss
git commit -m "style: add library toolbar, detail, selected row, playing indicator rules"
```

---

## Task 2: filter_entries pure function (TDD)

**Files:**
- Modify: `src/widgets/library_panel.py` (add module-level function before the classes)
- Create: `tests/test_library_panel.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_library_panel.py`:

```python
import os
import pytest

ENTRIES = [
    {
        "id": "1",
        "filename": "hello_world.wav",
        "voice_path": "voices/alice.wav",
        "text": "Hello world",
    },
    {
        "id": "2",
        "filename": "goodbye.wav",
        "voice_path": "voices/bob.wav",
        "text": "Goodbye friend",
    },
    {
        "id": "3",
        "filename": "alice_test.wav",
        "voice_path": "voices/alice.wav",
        "text": "Test phrase",
    },
]


def test_filter_no_constraints():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "Newest first")
    assert result == ENTRIES


def test_filter_by_voice():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "alice.wav", "Newest first")
    assert len(result) == 2
    assert all(os.path.basename(e["voice_path"]) == "alice.wav" for e in result)


def test_filter_by_search_filename():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "hello", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_filter_by_search_text():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "goodbye", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_filter_search_case_insensitive():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "HELLO", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_sort_oldest_first():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "Oldest first")
    assert [e["id"] for e in result] == ["3", "2", "1"]


def test_sort_by_voice_az():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "By voice A→Z")
    voices = [os.path.basename(e["voice_path"]) for e in result]
    assert voices == sorted(voices)


def test_filter_combined_voice_and_search():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "test", "alice.wav", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "3"


def test_filter_no_match_returns_empty():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "zzznomatch", "All voices", "Newest first")
    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_library_panel.py -v
```

Expected: FAIL with `ImportError: cannot import name 'filter_entries'`

- [ ] **Step 3: Add filter_entries to library_panel.py**

Open `src/widgets/library_panel.py`. Insert this function **before** the `class LibraryEntryWidget` line (after the imports at the top):

```python
def filter_entries(
    entries: list[dict], search: str, voice: str, sort: str
) -> list[dict]:
    """Pure filter + sort — no Qt, fully testable."""
    visible = entries

    if voice != "All voices":
        visible = [
            e for e in visible
            if os.path.basename(e.get("voice_path", "")) == voice
        ]

    if search:
        q = search.lower()
        visible = [
            e for e in visible
            if q in e.get("filename", "").lower()
            or q in e.get("text", "").lower()
        ]

    if sort == "Oldest first":
        visible = list(reversed(visible))
    elif sort == "By voice A→Z":
        visible = sorted(
            visible,
            key=lambda e: os.path.basename(e.get("voice_path", "")).lower(),
        )

    return visible
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_library_panel.py -v
```

Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/widgets/library_panel.py tests/test_library_panel.py
git commit -m "feat: add filter_entries pure function with tests"
```

---

## Task 3: Rewrite LibraryEntryWidget

**Files:**
- Modify: `src/widgets/library_panel.py` — replace the `LibraryEntryWidget` class entirely

The new widget removes the delete button, adds selection via `mousePressEvent`, and adds a `set_selected` method that refreshes the QSS objectName.

- [ ] **Step 1: Replace the LibraryEntryWidget class**

In `src/widgets/library_panel.py`, replace the entire `LibraryEntryWidget` class (lines 19–69 in the original file) with:

```python
class LibraryEntryWidget(QWidget):
    play_requested = pyqtSignal(str)    # filename
    row_selected = pyqtSignal(object)   # entry dict
    row_deselected = pyqtSignal()

    def __init__(self, entry: dict, row_index: int, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._row_index = row_index
        self._is_selected = False
        self._update_object_name()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        filename_label = QLabel(entry.get("filename", ""))
        filename_label.setMinimumWidth(160)

        voice_label = QLabel(os.path.basename(entry.get("voice_path", "")))
        voice_label.setMinimumWidth(110)

        text = entry.get("text", "")
        truncated = text[:50] + "…" if len(text) > 50 else text
        text_label = QLabel(truncated)
        text_label.setToolTip(text)

        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.clicked.connect(
            lambda: self.play_requested.emit(entry.get("filename", ""))
        )

        layout.addWidget(filename_label)
        layout.addWidget(voice_label)
        layout.addWidget(text_label)
        layout.addStretch()
        layout.addWidget(play_btn)

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._update_object_name()
        self.style().unpolish(self)
        self.style().polish(self)

    def _update_object_name(self) -> None:
        if self._is_selected:
            self.setObjectName("libraryRowSelected")
        else:
            self.setObjectName(
                "libraryRowEven" if self._row_index % 2 == 0 else "libraryRowOdd"
            )

    def mousePressEvent(self, event) -> None:
        if self._is_selected:
            self.row_deselected.emit()
        else:
            self.row_selected.emit(self._entry)
        super().mousePressEvent(event)
```

- [ ] **Step 2: Update the imports at the top of library_panel.py**

The file currently imports `QMessageBox` and `QPushButton` — those are still needed. Add `QLineEdit` to the imports since the detail panel needs it (Task 4 will use it). Also ensure `Qt` is imported from `PyQt6.QtCore`. Replace the imports block at the top of the file:

```python
import os
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.audio import OUTPUT_DIR
```

- [ ] **Step 3: Commit**

```bash
git add src/widgets/library_panel.py
git commit -m "feat: rewrite LibraryEntryWidget with selection signals, remove delete button"
```

---

## Task 4: Add LibraryDetailPanel class

**Files:**
- Modify: `src/widgets/library_panel.py` — insert new class after `LibraryEntryWidget`, before `LibraryPanel`

- [ ] **Step 1: Insert LibraryDetailPanel class**

In `src/widgets/library_panel.py`, insert this class **between** the end of `LibraryEntryWidget` and the start of `LibraryPanel`:

```python
class LibraryDetailPanel(QWidget):
    file_renamed = pyqtSignal(str, str)  # old_path, new_name
    entry_deleted = pyqtSignal(str)      # entry id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("libraryDetail")
        self._entry: dict | None = None
        self.setVisible(False)
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Top row: full text + right-aligned metadata
        top_row = QHBoxLayout()
        self._text_label = QLabel()
        self._text_label.setWordWrap(True)
        self._meta_label = QLabel()
        self._meta_label.setObjectName("statusLabel")
        self._meta_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        top_row.addWidget(self._text_label, stretch=1)
        top_row.addWidget(self._meta_label)
        layout.addLayout(top_row)

        # Bottom row: rename field + playing indicator + delete button
        bottom_row = QHBoxLayout()
        self._rename_edit = QLineEdit()
        self._rename_edit.editingFinished.connect(self._on_rename)

        self._playing_label = QLabel("▶ playing")
        self._playing_label.setObjectName("libraryPlayingIndicator")
        self._playing_label.setVisible(False)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setFixedWidth(70)
        self._delete_btn.clicked.connect(self._on_delete)

        bottom_row.addWidget(self._rename_edit, stretch=1)
        bottom_row.addWidget(self._playing_label)
        bottom_row.addWidget(self._delete_btn)
        layout.addLayout(bottom_row)

    def load_entry(self, entry: dict) -> None:
        self._entry = entry

        self._text_label.setText(entry.get("text", ""))

        settings = entry.get("settings", {})
        cfg = settings.get("cfg_value", "—")
        steps = settings.get("inference_timesteps", "—")
        denoiser = "denoiser on" if settings.get("use_denoiser") else "denoiser off"
        created = entry.get("created_at", "")[:16].replace("T", " ")
        self._meta_label.setText(
            f"{created} · cfg {cfg} · {steps} steps · {denoiser}"
        )

        stem = Path(entry.get("filename", "")).stem
        self._rename_edit.blockSignals(True)
        self._rename_edit.setText(stem)
        self._rename_edit.blockSignals(False)

        self._playing_label.setVisible(False)
        self.setVisible(True)

    def clear(self) -> None:
        self._entry = None
        self.setVisible(False)

    def set_playing(self, playing: bool) -> None:
        self._playing_label.setVisible(playing)

    def _on_rename(self) -> None:
        if self._entry is None:
            return
        new_name = self._rename_edit.text().strip()
        if not new_name:
            return
        old_filename = self._entry.get("filename", "")
        old_stem = Path(old_filename).stem
        if new_name == old_stem:
            return
        # Update _entry immediately so a second editingFinished is a no-op
        suffix = Path(old_filename).suffix
        self._entry = dict(self._entry)
        self._entry["filename"] = new_name + suffix
        old_path = str(OUTPUT_DIR / old_filename)
        self.file_renamed.emit(old_path, new_name)

    def _on_delete(self) -> None:
        if self._entry is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete {self._entry.get('filename', 'this file')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            entry_id = self._entry.get("id", "")
            if entry_id:
                self.entry_deleted.emit(entry_id)
```

- [ ] **Step 2: Commit**

```bash
git add src/widgets/library_panel.py
git commit -m "feat: add LibraryDetailPanel with rename, delete, metadata, playing indicator"
```

---

## Task 5: Rewrite LibraryPanel

**Files:**
- Modify: `src/widgets/library_panel.py` — replace the `LibraryPanel` class entirely

- [ ] **Step 1: Replace the LibraryPanel class**

In `src/widgets/library_panel.py`, replace the entire `LibraryPanel` class with:

```python
class LibraryPanel(QWidget):
    entry_deleted = pyqtSignal(str)      # entry id
    file_renamed = pyqtSignal(str, str)  # old_path, new_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[dict] = []
        self._selected_widget: LibraryEntryWidget | None = None
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # Toolbar strip
        toolbar = QWidget()
        toolbar.setObjectName("libraryToolbar")
        toolbar_row = QHBoxLayout(toolbar)
        toolbar_row.setContentsMargins(0, 0, 0, 6)
        toolbar_row.setSpacing(8)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search…")
        self._search_box.textChanged.connect(self._apply_filter)

        self._voice_filter = QComboBox()
        self._voice_filter.setMinimumWidth(160)
        self._voice_filter.currentIndexChanged.connect(self._apply_filter)

        self._sort_combo = QComboBox()
        self._sort_combo.setMinimumWidth(130)
        self._sort_combo.addItems(["Newest first", "Oldest first", "By voice A→Z"])
        self._sort_combo.currentIndexChanged.connect(self._apply_filter)

        toolbar_row.addWidget(self._search_box, stretch=1)
        toolbar_row.addWidget(self._voice_filter)
        toolbar_row.addWidget(self._sort_combo)
        layout.addWidget(toolbar)

        # Header row
        header = QWidget()
        header.setObjectName("libraryHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        for col_text, min_w in [("Title", 160), ("Voice", 110), ("Description", 0)]:
            lbl = QLabel(f"<b>{col_text}</b>")
            if min_w:
                lbl.setMinimumWidth(min_w)
            header_layout.addWidget(lbl)
        header_layout.addStretch()
        header_layout.addSpacing(40)  # align with play button column
        layout.addWidget(header)

        # Scrollable table
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)

        # Detail panel
        self._detail = LibraryDetailPanel()
        self._detail.file_renamed.connect(self.file_renamed)
        self._detail.entry_deleted.connect(self._on_detail_delete)
        layout.addWidget(self._detail)

        # Playback state drives playing indicator
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

    def load_entries(self, entries: list[dict]) -> None:
        self._all_entries = entries
        self._rebuild_voice_filter()
        self._apply_filter()

    def _rebuild_voice_filter(self) -> None:
        voices = sorted({
            os.path.basename(e.get("voice_path", ""))
            for e in self._all_entries
            if e.get("voice_path")
        })
        current = self._voice_filter.currentText()
        self._voice_filter.blockSignals(True)
        self._voice_filter.clear()
        self._voice_filter.addItem("All voices")
        for v in voices:
            self._voice_filter.addItem(v)
        idx = self._voice_filter.findText(current)
        self._voice_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self._voice_filter.blockSignals(False)

    def _apply_filter(self) -> None:
        search = self._search_box.text().strip()
        voice = self._voice_filter.currentText()
        sort = self._sort_combo.currentText()
        visible = filter_entries(self._all_entries, search, voice, sort)

        # Clear selection whenever the list rebuilds
        self._selected_widget = None
        self._detail.clear()

        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, entry in enumerate(visible):
            widget = LibraryEntryWidget(entry, i)
            widget.play_requested.connect(self._on_play_requested)
            widget.row_selected.connect(
                lambda e, w=widget: self._on_row_selected(e, w)
            )
            widget.row_deselected.connect(self._on_row_deselected)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, widget
            )

    def _on_row_selected(
        self, entry: dict, widget: LibraryEntryWidget
    ) -> None:
        if self._selected_widget is not None and self._selected_widget is not widget:
            self._selected_widget.set_selected(False)
        self._selected_widget = widget
        widget.set_selected(True)
        self._detail.load_entry(entry)

    def _on_row_deselected(self) -> None:
        if self._selected_widget is not None:
            self._selected_widget.set_selected(False)
        self._selected_widget = None
        self._detail.clear()

    def _on_play_requested(self, filename: str) -> None:
        path = str(OUTPUT_DIR / filename)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def _on_playback_state_changed(
        self, state: QMediaPlayer.PlaybackState
    ) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self._detail.set_playing(playing)

    def _on_detail_delete(self, entry_id: str) -> None:
        self._selected_widget = None
        self.entry_deleted.emit(entry_id)
```

- [ ] **Step 2: Run existing tests to make sure nothing is broken**

```bash
pytest tests/ -v
```

Expected: all tests in `test_library.py`, `test_library_panel.py`, `test_audio.py`, `test_config.py`, `test_ollama.py` PASS

- [ ] **Step 3: Run the app and verify the library tab manually**

```bash
python main.py
```

Check:
- Library tab shows toolbar (search box, voice filter, sort combo)
- Header row with Title / Voice / Description labels
- Entries listed as rows with filename, voice, text, ▶ button
- Clicking a row highlights it and shows the detail panel at the bottom
- Detail panel shows full text, metadata (date · cfg · steps · denoiser), filename stem in rename field
- Clicking the selected row again hides the detail panel
- ▶ button plays audio; "▶ playing" label appears in detail panel while playing

- [ ] **Step 4: Commit**

```bash
git add src/widgets/library_panel.py
git commit -m "feat: rewrite LibraryPanel with toolbar, selection, detail panel"
```

---

## Task 6: Wire file_renamed in app.py

**Files:**
- Modify: `src/app.py` — add one line to `_setup_ui`

The current `app.py` only wires `entry_deleted` from `LibraryPanel`. The new `file_renamed` signal needs to be connected to the existing `_on_file_renamed` handler.

- [ ] **Step 1: Add the file_renamed connection**

In `src/app.py`, find this block in `_setup_ui` (around line 95):

```python
        self._library_panel.entry_deleted.connect(self._on_library_entry_deleted)
```

Add the new connection directly after it:

```python
        self._library_panel.entry_deleted.connect(self._on_library_entry_deleted)
        self._library_panel.file_renamed.connect(self._on_file_renamed)
```

- [ ] **Step 2: Run the app and verify rename end-to-end**

```bash
python main.py
```

Check:
- Generate a clip (or open Library with existing entries)
- Click a row to open detail panel
- Edit the filename field, press Enter
- Verify: file is renamed on disk, library list updates with new filename, detail panel closes (list rebuilds)

- [ ] **Step 3: Commit**

```bash
git add src/app.py
git commit -m "feat: wire LibraryPanel.file_renamed to app rename handler"
```

---

## Done

All six tasks complete. The library now has:
- Toolbar: search + voice filter + sort preset
- Clean table rows: filename, voice, text, play button only
- Selection: click row → detail panel; click again → deselect
- Detail panel: full text, metadata, rename field, delete button, playing indicator
- Filtering and sorting applied simultaneously across all three controls
