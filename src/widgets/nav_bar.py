from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavBar(QWidget):
    view_changed = pyqtSignal(int)  # 0 = Generate, 1 = Library, 2 = Voices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 0)

        self._generate_btn = QPushButton("Generate")
        self._library_btn = QPushButton("Library")
        self._voices_btn = QPushButton("Voices")

        for btn in (self._generate_btn, self._library_btn, self._voices_btn):
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            layout.addWidget(btn)

        self._generate_btn.setChecked(True)
        layout.addStretch()

        self._generate_btn.clicked.connect(lambda: self._select(0))
        self._library_btn.clicked.connect(lambda: self._select(1))
        self._voices_btn.clicked.connect(lambda: self._select(2))

    def _select(self, index: int) -> None:
        self._generate_btn.setChecked(index == 0)
        self._library_btn.setChecked(index == 1)
        self._voices_btn.setChecked(index == 2)
        self.view_changed.emit(index)
