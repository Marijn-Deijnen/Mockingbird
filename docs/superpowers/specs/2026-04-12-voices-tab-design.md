# Voices Tab Design

## Goal

Add a third "Voices" tab to the nav bar: a voice management panel where users can import voice files, give them display names, audition them, rename them, and delete them.

---

## Data Model

**File:** `src/voices.py`  
**Store:** `audio/voices.json`

Each entry:
```json
{
  "id": "<uuid-stem>",
  "filename": "david_attenborough.wav",
  "display_name": "David Attenborough"
}
```

Functions:
- `load() -> list[dict]`
- `save(entries: list[dict]) -> None`
- `add_voice(entry: dict) -> list[dict]` — prepends, saves, returns updated list
- `rename_voice(voice_id: str, display_name: str) -> list[dict]`
- `delete_voice(voice_id: str) -> list[dict]`

`VOICES_PATH = Path(__file__).parent.parent / "audio" / "voices.json"`

---

## Import Flow

1. User clicks **Add Voice** in the toolbar
2. `QFileDialog.getOpenFileName` — filter `Audio Files (*.wav *.mp3)`
3. Selected file is copied into `audio/` with a sanitized filename (strip forbidden chars). If the filename already exists, append `_2`, `_3`, etc.
4. `QInputDialog.getText` — prompt "Display name:", pre-filled with the file stem
5. If user cancels the name prompt: delete the copied file, abort
6. Generate a UUID-based id (`uuid.uuid4().hex[:8]`)
7. Call `voices.add_voice({id, filename, display_name})`, refresh list

---

## Nav Bar

`NavBar` adds a third `QPushButton("Voices")` with `setObjectName("navBtn")` and `setCheckable(True)`. `_select(index)` already handles arbitrary indices — no change to logic, just add the button and connect `clicked → lambda: self._select(2)`.

---

## VoicesPanel Layout

**File:** `src/widgets/voices_panel.py`

Vertical layout:

1. **Toolbar** — `QWidget`, objectName `voicesToolbar`, horizontal row:
   - `QPushButton("Add Voice")` — left-aligned
   - `addStretch()`

2. **Header row** — `QWidget`, objectName `libraryHeader` (reuse existing QSS):
   - Bold labels: Name (fixed 180px), File (fixed 160px), Format (fixed 50px)
   - `addStretch()` then `addSpacing(104)` to align with 3 buttons (32×3 + spacing)

3. **Scroll area** → content widget → `QVBoxLayout` with `addStretch()`

4. Each row is a `VoiceEntryWidget` with alternating `libraryRowEven` / `libraryRowOdd` objectNames (reuse existing QSS)

`VoicesPanel` owns `QMediaPlayer` + `QAudioOutput` for auditioning.

**`VoicesPanel` public methods:**
- `load_voices(entries: list[dict]) -> None` — stores entries, rebuilds the list
- (internal) `_rebuild_list()` — clears and repopulates the scroll area

---

## VoiceEntryWidget

**Signals:** `play_requested = pyqtSignal(str)`, `rename_requested = pyqtSignal(str, str)`, `delete_requested = pyqtSignal(str)`

**Columns:**
- Display name label — fixed 180px; replaced by `QLineEdit` during inline rename
- Filename label — fixed 160px
- Format label — fixed 50px (`"WAV"` or `"MP3"`, uppercase from suffix)

**Buttons (right side, each fixed 32px):**
- `▶` — emits `play_requested(filename)`
- `✎` — triggers inline rename mode
- `✕` — `QMessageBox.question` confirmation, then emits `delete_requested(voice_id)`

**Inline rename:**
- `✎` clicked: hide display name label, show `QLineEdit` pre-filled with current display name
- On `editingFinished`: if text non-empty and changed, emit `rename_requested(voice_id, new_name)`; update `self._display_name` immediately (double-fire guard — same pattern as `LibraryDetailPanel._on_rename`); restore label with new name; hide line edit
- If text empty or unchanged: just restore label, no emit

---

## QSS Additions

```css
QWidget#voicesToolbar {
    border-bottom: 1px solid #2a2f3a;
    padding-bottom: 6px;
}
```

All other styling (rows, header, nav button) reuses existing rules.

---

## app.py Changes

- Import `VoicesPanel` and `voices` module
- In `_setup_ui`: create `self._voices_panel = VoicesPanel()`, call `self._voices_panel.load_voices(voices.load())`, add as page 2 of `self._stack`
- No new signal connections needed (nav bar `view_changed → stack.setCurrentIndex` already handles all indices)

---

## Files

| File | Change |
|------|--------|
| `src/voices.py` | New — data module |
| `src/widgets/voices_panel.py` | New — VoicesPanel + VoiceEntryWidget |
| `src/widgets/nav_bar.py` | Add Voices button |
| `src/assets/style.qss` | Add `voicesToolbar` rule |
| `src/app.py` | Import + wire VoicesPanel |
| `tests/test_voices.py` | Tests for voices.py CRUD functions |

---

## Out of Scope

- Linking voices to the Generate tab's Reference panel (browse/select stays separate)
- Voice profiles (per-voice generation settings — separate feature)
- Waveform preview or duration display
- Bulk import
