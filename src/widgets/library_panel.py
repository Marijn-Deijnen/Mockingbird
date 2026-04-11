import os

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.audio import OUTPUT_DIR


class LibraryEntryWidget(QWidget):
    delete_requested = pyqtSignal(str)  # entry id
    play_requested = pyqtSignal(str)    # filename (not full path)

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self._entry = entry

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        filename_label = QLabel(entry.get("filename", ""))
        filename_label.setMinimumWidth(160)

        voice_label = QLabel(os.path.basename(entry.get("voice_path", "")))
        voice_label.setMinimumWidth(110)

        text = entry.get("text", "")
        truncated = text[:30] + "…" if len(text) > 30 else text
        text_label = QLabel(truncated)
        text_label.setToolTip(text)
        text_label.setMinimumWidth(200)

        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(32)

        layout.addWidget(filename_label)
        layout.addWidget(voice_label)
        layout.addWidget(text_label)
        layout.addStretch()
        layout.addWidget(play_btn)
        layout.addWidget(delete_btn)

        play_btn.clicked.connect(
            lambda: self.play_requested.emit(entry.get("filename", ""))
        )
        delete_btn.clicked.connect(self._on_delete)

    def _on_delete(self):
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete {self._entry.get('filename', 'this file')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            entry_id = self._entry.get("id", "")
            if entry_id:
                self.delete_requested.emit(entry_id)


class LibraryPanel(QWidget):
    entry_deleted = pyqtSignal(str)  # entry id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[dict] = []
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter by voice:"))
        self._voice_filter = QComboBox()
        self._voice_filter.setMinimumWidth(200)
        self._voice_filter.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(self._voice_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Header row
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        for text, min_width in [("Title", 160), ("Voice", 110), ("Description", 200)]:
            lbl = QLabel(f"<b>{text}</b>")
            lbl.setMinimumWidth(min_width)
            header_layout.addWidget(lbl)
        header_layout.addStretch()
        # Spacer to align with play/delete buttons (32 + 32 + spacing)
        header_layout.addSpacing(72)
        layout.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)

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
        selected = self._voice_filter.currentText()
        if selected == "All voices":
            visible = self._all_entries
        else:
            visible = [
                e for e in self._all_entries
                if os.path.basename(e.get("voice_path", "")) == selected
            ]

        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for entry in visible:
            widget = LibraryEntryWidget(entry)
            widget.delete_requested.connect(self.entry_deleted)
            widget.play_requested.connect(self._on_play_requested)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, widget
            )

    def _on_play_requested(self, filename: str) -> None:
        path = str(OUTPUT_DIR / filename)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
