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
