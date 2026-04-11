from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from src.ollama import OllamaWorker


class AIPanel(QGroupBox):
    result_ready = pyqtSignal(str)

    def __init__(self, host: str, port: int, model: str, parent=None):
        super().__init__("AI Prompt", parent)
        self._host = host
        self._port = port
        self._model = model
        self._worker: OllamaWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._prompt_edit = QPlainTextEdit()
        self._prompt_edit.setPlaceholderText(
            "Describe what you want the AI to say..."
        )
        self._prompt_edit.setMinimumHeight(80)
        layout.addWidget(self._prompt_edit)

        controls = QHBoxLayout()
        self._ask_btn = QPushButton("Ask AI")
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(120)
        controls.addWidget(self._ask_btn)
        controls.addWidget(self._progress)
        controls.addStretch()
        layout.addLayout(controls)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._ask_btn.clicked.connect(self._on_ask)

    def update_config(self, host: str, port: int, model: str):
        self._host = host
        self._port = port
        self._model = model

    def _on_ask(self):
        prompt = self._prompt_edit.toPlainText().strip()
        if not prompt:
            self._status_label.setText("Please enter a prompt.")
            return
        if not self._model:
            self._status_label.setText(
                "No model selected. Open Settings → AI Settings to connect."
            )
            return
        if self._worker is not None and self._worker.isRunning():
            return

        self._ask_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("")

        self._worker = OllamaWorker(
            text=prompt,
            host=self._host,
            port=self._port,
            model=self._model,
        )
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, text: str):
        self._worker.wait()
        self._ask_btn.setEnabled(True)
        self._progress.setVisible(False)
        self.result_ready.emit(text)

    def _on_error(self, message: str):
        self._worker.wait()
        self._ask_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(f"Error: {message}")

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            if not self._worker.wait(3000):
                self._worker.terminate()
        super().closeEvent(event)
