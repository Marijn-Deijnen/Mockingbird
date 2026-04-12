# Library Overhaul Design

## Goal

Replace the current flat filter-list library with a file-manager-style table: toolbar strip (search + voice filter + sort), clean data rows with inline play, and a collapsible detail panel at the bottom for rename/delete/metadata.

---

## Structure

The `LibraryPanel` widget splits into four vertical zones stacked in a `QVBoxLayout`:

1. **Toolbar strip** — search + voice filter + sort controls
2. **Header row** — bold column labels, non-interactive
3. **Table** — scrollable list of `LibraryEntryWidget` rows
4. **Detail panel** — fixed-height strip, hidden when no row is selected

---

## Toolbar Strip

Widget: `QWidget`, objectName `libraryToolbar`  
Layout: `QHBoxLayout`, single horizontal row

Controls (left to right):
- `QLineEdit` — placeholder `"Search…"`, grows to fill available space via stretch; filters on `textChanged` against filename stem and full entry text
- `QComboBox` — voice filter, min-width 160px, "All voices" + one item per unique voice basename
- `QComboBox` — sort preset, min-width 130px, items: `"Newest first"`, `"Oldest first"`, `"By voice A→Z"`

All three controls apply simultaneously: every change to any control calls `_apply_filter()` which filters and sorts `_all_entries` and rebuilds the visible rows.

---

## Header Row

Widget: `QWidget`, objectName `libraryHeader`  
Same as current: bold Filename / Voice / Text labels with matching min-widths (160 / 110 / —).  
Bottom border separator via QSS.

---

## Table Rows (`LibraryEntryWidget`)

Columns:
- **Filename** — `QLabel`, min-width 160px
- **Voice** — `QLabel`, min-width 110px (basename of voice_path)
- **Text** — `QLabel`, grows to fill remaining width (no fixed min-width); no truncation limit needed since the detail panel shows full text — truncate at 50 chars with `…` for row display
- **Play ▶** — `QPushButton`, fixed-width 32px, rightmost; clicking plays audio without affecting selection

Row selection:
- Clicking anywhere on the row except the play button selects it and emits `row_selected = pyqtSignal(dict)` with the entry dict
- Selected row background: `#313848` (objectName `libraryRowSelected`)
- Clicking the already-selected row deselects it (emits `row_deselected = pyqtSignal()`)
- Alternating even/odd background for unselected rows: `libraryRowEven` / `libraryRowOdd` as today

Signals:
- `play_requested = pyqtSignal(str)` — filename
- `row_selected = pyqtSignal(dict)` — full entry dict
- `row_deselected = pyqtSignal()`

---

## Detail Panel

Widget: `QWidget`, objectName `libraryDetail`  
Height: fixed 120px  
Visibility: hidden by default; shown via `setVisible(True)` when a row is selected

Top border separator via QSS (`border-top: 1px solid #3a4150`).

Layout: `QVBoxLayout` with two `QHBoxLayout` sub-rows.

**Top row:**
- `QLabel` — full entry text, word-wrap enabled, grows horizontally
- `QLabel` — right-aligned metadata: `"created_at · cfg X.X · N steps · denoiser on/off"`, styled as `statusLabel` (monospace, 10px, `#a0aabf`)

**Bottom row:**
- `QLineEdit` — pre-filled with filename stem (no extension); confirms rename on `returnPressed` and `editingFinished`; left-aligned, grows horizontally
- `QLabel` — playback indicator, objectName `libraryPlayingIndicator`; text `"▶ playing"`, amber color (`#e8a838`), hidden when not playing; shown while `QMediaPlayer` state is `PlayingState`, hidden on stop/end
- `QPushButton` — `"Delete"`, fixed-width, rightmost; triggers confirmation dialog then emits `entry_deleted`

---

## Audio Playback

`QMediaPlayer` + `QAudioOutput` remain in `LibraryPanel` (not per-row).  
`playbackStateChanged` signal on `QMediaPlayer` drives the `libraryPlayingIndicator` label visibility in the detail panel.  
Playing a new row while another is playing stops the previous one (Qt default behaviour — setting a new source stops playback).

---

## Filtering and Sorting

`_apply_filter()` reads all three toolbar controls and rebuilds visible rows:

```python
def _apply_filter(self) -> None:
    search = self._search_box.text().strip().lower()
    voice = self._voice_filter.currentText()
    sort = self._sort_combo.currentText()

    visible = self._all_entries

    if voice != "All voices":
        visible = [e for e in visible if os.path.basename(e.get("voice_path", "")) == voice]

    if search:
        visible = [
            e for e in visible
            if search in e.get("filename", "").lower()
            or search in e.get("text", "").lower()
        ]

    if sort == "Oldest first":
        visible = list(reversed(visible))  # data is newest-first in JSON
    elif sort == "By voice A→Z":
        visible = sorted(visible, key=lambda e: os.path.basename(e.get("voice_path", "")).lower())

    # rebuild rows...
```

---

## Rename Flow

1. User edits `QLineEdit` in detail panel
2. On `returnPressed` or `editingFinished`: read new value, strip whitespace
3. If unchanged or empty: no-op
4. Emit `file_renamed = pyqtSignal(str, str)` — `(old_path, new_name)` — same signature as today so `app.py` wiring requires no changes

---

## Delete Flow

1. User clicks Delete in detail panel
2. `QMessageBox.question` confirmation (same as today)
3. On confirm: emit `entry_deleted = pyqtSignal(str)` with entry id
4. Detail panel hides, selection cleared

---

## QSS Additions

```css
QWidget#libraryToolbar {
    border-bottom: 1px solid #2a2f3a;
    padding-bottom: 6px;
}

QWidget#libraryDetail {
    border-top: 1px solid #3a4150;
    padding-top: 6px;
}

QWidget#libraryRowSelected {
    background-color: #313848;
}

QLabel#libraryPlayingIndicator {
    color: #e8a838;
    font-size: 10px;
    font-family: "Consolas", "Courier New", monospace;
}
```

---

## Files Changed

- `src/widgets/library_panel.py` — full rewrite of `LibraryPanel` and `LibraryEntryWidget`
- `src/assets/style.qss` — add `libraryToolbar`, `libraryDetail`, `libraryRowSelected`, `libraryPlayingIndicator` rules
- `src/app.py` — add one new connection: `self._library_panel.file_renamed.connect(self._on_file_renamed)`; `_on_file_renamed` signature is unchanged so no other edits needed

`LibraryPanel` must declare `file_renamed = pyqtSignal(str, str)` at class level (old_path, new_name) — same signature as `OutputPanel.file_renamed` so the existing `_on_file_renamed` handler in `app.py` works without modification.

---

## Out of Scope

- Bulk selection / multi-delete
- Export or copy-to-clipboard
- Inline audio waveform / duration display
- Keyboard navigation between rows
