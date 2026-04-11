from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QPlainTextEdit


class TextPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Text to Speak", parent)
        layout = QVBoxLayout(self)
        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText("Enter text to speak...")
        self._text_edit.setMinimumHeight(100)
        layout.addWidget(self._text_edit)

    def text(self) -> str:
        return self._text_edit.toPlainText().strip()
