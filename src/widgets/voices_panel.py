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
        if not self._name_edit.isVisible():
            return
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
    voices_changed = pyqtSignal(list)  # emits updated entries list after any mutation

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
            dest.unlink(missing_ok=True)
            return

        entry = {
            "id": uuid.uuid4().hex[:8],
            "filename": dest.name,
            "display_name": display_name.strip(),
        }
        entries = voices.add_voice(entry)
        self.load_voices(entries)
        self.voices_changed.emit(entries)

    def _on_play_requested(self, filename: str) -> None:
        path = str(VOICES_DIR / filename)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def _on_rename_requested(self, voice_id: str, new_name: str) -> None:
        # Widget already updated its own label; just persist to disk
        self._all_entries = voices.rename_voice(voice_id, new_name)
        self.voices_changed.emit(self._all_entries)

    def _on_delete_requested(self, voice_id: str) -> None:
        entry = next((e for e in self._all_entries if e["id"] == voice_id), None)
        if entry:
            file_path = VOICES_DIR / entry["filename"]
            if file_path.exists():
                file_path.unlink()
        entries = voices.delete_voice(voice_id)
        self.load_voices(entries)
        self.voices_changed.emit(entries)
