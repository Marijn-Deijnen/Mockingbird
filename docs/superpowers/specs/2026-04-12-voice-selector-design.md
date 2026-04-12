# Voice Selector & Button Visibility Design

## Goal

Two changes in one branch:

1. **Button visibility fix** — 32px icon buttons (▶ / ✎ / ✕) in the Voices and Library panels are nearly invisible because the global `QPushButton` style applies `padding: 5px 14px`, leaving ~4px for the symbol. Fix by naming these buttons and adding a tight-padding rule.

2. **Voice Selector** — Replace the `ReferencePanel` (browse + recents) on the Generate tab with a `VoiceSelector` dropdown backed by `voices.json`. Per-voice generation settings (cfg, steps, denoiser) carry over, keyed by voice ID instead of file path.

---

## Button Visibility Fix

**Files:** `src/widgets/voices_panel.py`, `src/widgets/library_panel.py`, `src/assets/style.qss`

All 32px icon buttons receive `setObjectName("iconBtn")`. New QSS rule:

```css
QPushButton#iconBtn {
    padding: 2px 0px;
    font-size: 13px;
}
```

This applies to: ▶ / ✎ / ✕ in `VoiceEntryWidget`, ▶ in `LibraryEntryWidget`.

---

## VoiceSelector Widget

**File:** `src/widgets/voice_selector.py`

```python
class VoiceSelector(QWidget):
    voice_changed = pyqtSignal(str, str)  # voice_id, absolute_path
```

**Layout:** `QHBoxLayout` — `QLabel("Voice:")` (fixed 50px) + `QComboBox` (stretches).

**Empty state:** combo `setEnabled(False)`, `setPlaceholderText("No voices — import one in the Voices tab")`.

**Internal state:** stores `_entries: list[dict]` (id, filename, display_name).

**Methods:**
- `refresh(entries: list[dict]) -> None` — repopulates combo; remembers the current voice ID before clearing, then restores that selection if still present; otherwise selects index 0 (or shows placeholder if empty)
- `select_by_id(voice_id: str) -> None` — selects the combo item whose entry ID matches; no-op if not found; used once at startup to restore `last_voice_id` from config
- `current_voice_id() -> str | None` — returns `_entries[combo.currentIndex()]["id"]` or None
- `current_path() -> str | None` — returns `str(VOICES_DIR / filename)` or None

**Signal emission:** `currentIndexChanged` → look up entry by index → emit `voice_changed(id, path)`.

`ReferencePanel` (`src/widgets/reference_panel.py`) is deleted.

---

## VoicesPanel — voices_changed signal

**File:** `src/widgets/voices_panel.py`

Add class-level signal:
```python
voices_changed = pyqtSignal(list)  # updated entries list
```

Emit after every mutation:
- `_on_add_voice` — after `self.load_voices(entries)`, emit `self.voices_changed.emit(entries)`
- `_on_rename_requested` — after `self._all_entries = voices.rename_voice(...)`, emit `self.voices_changed.emit(self._all_entries)`
- `_on_delete_requested` — after `self.load_voices(entries)`, emit `self.voices_changed.emit(entries)`

---

## app.py Changes

**Imports:** Remove `ReferencePanel`, add `VoiceSelector`.

**`_setup_ui`:**
- Replace `self._ref_panel = ReferencePanel(self._cfg)` with:
  ```python
  self._voice_selector = VoiceSelector()
  self._voice_selector.refresh(voices.load())
  if self._cfg.get("last_voice_id"):
      self._voice_selector.select_by_id(self._cfg["last_voice_id"])
  ```
- Remove `self._ref_panel.reference_changed.connect(self._on_reference_changed)`
- Add `self._voice_selector.voice_changed.connect(self._on_voice_changed)`
- Add `self._voices_panel.voices_changed.connect(self._voice_selector.refresh)`

**`_on_voice_changed(voice_id: str, path: str)`** (replaces `_on_reference_changed`):
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

**`_on_settings_changed`:** change profile key from `current_voice` (path) to `voice_id`:
```python
current_voice_id = self._voice_selector.current_voice_id()
if current_voice_id:
    self._cfg["voice_profiles"][current_voice_id] = {
        "cfg_value": values["cfg_value"],
        "inference_timesteps": values["inference_timesteps"],
        "use_denoiser": values["use_denoiser"],
    }
```

**`_on_generate`:** change `ref_path = self._ref_panel.current_path()` to `ref_path = self._voice_selector.current_path()`. Change warning to `"Please select a voice."`.

---

## config.py Changes

**`DEFAULTS`:** Remove `last_reference` and `recent_references` keys; add `"last_voice_id": ""`.

**Delete** `add_recent_reference` function (no callers remain).

---

## QSS

Button visibility rule added to `src/assets/style.qss` (see Button Visibility Fix section above). No other QSS changes needed.

---

## Files

| File | Change |
|------|--------|
| `src/widgets/voice_selector.py` | New |
| `src/widgets/voices_panel.py` | Add `voices_changed` signal + emit calls |
| `src/widgets/library_panel.py` | `setObjectName("iconBtn")` on play button |
| `src/widgets/reference_panel.py` | Deleted |
| `src/app.py` | Replace ref panel wiring, add voice selector wiring |
| `src/config.py` | Remove `last_reference`/`recent_references`, remove `add_recent_reference`, add `last_voice_id` |
| `src/assets/style.qss` | Add `iconBtn` rule |

---

## Out of Scope

- Migrating existing path-keyed `voice_profiles` entries (orphaned entries remain in config, unused)
- Any changes to the Library tab or how library entries store `voice_path`
- Voice preview from the Generate tab
