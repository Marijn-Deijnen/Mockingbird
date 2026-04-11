import os

from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal


class ReferencePanel(QGroupBox):
    reference_changed = pyqtSignal(str)  # emits absolute path

    def __init__(self, cfg: dict, parent=None):
        super().__init__("Reference Audio", parent)
        self._cfg = cfg
        self._current_path = ""
        self._setup_ui()
        if cfg.get("last_reference"):
            self._set_path(cfg["last_reference"])

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        browse_row = QHBoxLayout()
        self._browse_btn = QPushButton("Browse...")
        self._path_label = QLabel("No file selected")
        self._path_label.setWordWrap(True)
        browse_row.addWidget(self._browse_btn)
        browse_row.addWidget(self._path_label, 1)
        layout.addLayout(browse_row)

        self._recents_layout = QHBoxLayout()
        layout.addLayout(self._recents_layout)
        self._refresh_recents()

        self._browse_btn.clicked.connect(self._on_browse)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Audio", "", "Audio Files (*.wav *.mp3)"
        )
        if path:
            self._set_path(path)

    def _set_path(self, path: str):
        self._current_path = path
        self._path_label.setText(path)
        self.reference_changed.emit(path)

    def _refresh_recents(self):
        while self._recents_layout.count():
            item = self._recents_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for path in self._cfg.get("recent_references", []):
            name = os.path.basename(path)
            btn = QPushButton(name)
            btn.setFlat(True)
            btn.setToolTip(path)
            btn.clicked.connect(lambda checked, p=path: self._set_path(p))
            self._recents_layout.addWidget(btn)

        self._recents_layout.addStretch()

    def update_recents(self, cfg: dict):
        self._cfg = cfg
        self._refresh_recents()

    def current_path(self) -> str:
        return self._current_path
