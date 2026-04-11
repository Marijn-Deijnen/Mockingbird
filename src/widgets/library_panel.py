import os

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
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
            self.delete_requested.emit(self._entry["id"])


class LibraryPanel(QWidget):
    entry_deleted = pyqtSignal(str)  # entry id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)

    def load_entries(self, entries: list[dict]) -> None:
        # Remove all entry widgets (leave the trailing stretch)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for entry in entries:
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
