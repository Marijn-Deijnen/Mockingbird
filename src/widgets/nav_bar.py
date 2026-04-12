from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavBar(QWidget):
    view_changed = pyqtSignal(int)  # 0 = Generate, 1 = Library

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 0)

        self._generate_btn = QPushButton("Generate")
        self._library_btn = QPushButton("Library")
        self._generate_btn.setObjectName("navBtn")
        self._library_btn.setObjectName("navBtn")
        self._generate_btn.setCheckable(True)
        self._library_btn.setCheckable(True)
        self._generate_btn.setChecked(True)

        layout.addWidget(self._generate_btn)
        layout.addWidget(self._library_btn)
        layout.addStretch()

        self._generate_btn.clicked.connect(lambda: self._select(0))
        self._library_btn.clicked.connect(lambda: self._select(1))

    def _select(self, index: int) -> None:
        self._generate_btn.setChecked(index == 0)
        self._library_btn.setChecked(index == 1)
        self.view_changed.emit(index)
