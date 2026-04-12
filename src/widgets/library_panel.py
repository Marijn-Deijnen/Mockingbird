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


def _col_sep() -> QWidget:
    """1px vertical column separator."""
    sep = QWidget()
    sep.setFixedWidth(1)
    sep.setObjectName("colSep")
    return sep


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
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        filename_label = QLabel(entry.get("filename", ""))
        filename_label.setFixedWidth(160)

        voice_label = QLabel(os.path.basename(entry.get("voice_path", "")))
        voice_label.setFixedWidth(110)

        text = entry.get("text", "")
        truncated = text[:50] + "…" if len(text) > 50 else text
        text_label = QLabel(truncated)
        text_label.setToolTip(text)

        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)
        play_btn.setObjectName("iconBtn")
        play_btn.clicked.connect(
            lambda: self.play_requested.emit(entry.get("filename", ""))
        )

        layout.addWidget(filename_label)
        layout.addSpacing(8)
        layout.addWidget(_col_sep())
        layout.addSpacing(8)
        layout.addWidget(voice_label)
        layout.addSpacing(8)
        layout.addWidget(_col_sep())
        layout.addSpacing(8)
        layout.addWidget(text_label, stretch=1)
        layout.addSpacing(4)
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
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(0)
        for col_text, fixed_w in [("Title", 160), ("Voice", 110), ("Description", 0)]:
            lbl = QLabel(f"<b>{col_text}</b>")
            if fixed_w:
                lbl.setFixedWidth(fixed_w)
                header_layout.addWidget(lbl)
                header_layout.addSpacing(8)
                header_layout.addWidget(_col_sep())
                header_layout.addSpacing(8)
            else:
                header_layout.addWidget(lbl, stretch=1)
        header_layout.addSpacing(4)
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
        if self._selected_widget is not None:
            self._selected_widget.set_selected(False)
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
        if self._selected_widget is not None:
            self._selected_widget.set_selected(False)
        self._selected_widget = None
        self._detail.clear()
        self.entry_deleted.emit(entry_id)
