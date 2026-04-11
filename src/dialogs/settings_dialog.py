from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.ollama import fetch_models


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(340)
        self._setup_ui(cfg)

    def _setup_ui(self, cfg: dict):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._enabled_check = QCheckBox()
        self._enabled_check.setChecked(cfg.get("ollama_enabled", False))
        form.addRow("Enable AI Assistant", self._enabled_check)

        self._host_edit = QLineEdit(cfg.get("ollama_host", "127.0.0.1"))
        form.addRow("Host", self._host_edit)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(cfg.get("ollama_port", 11434))
        form.addRow("Port", self._port_spin)

        connect_row = QHBoxLayout()
        self._connect_btn = QPushButton("Connect")
        self._connect_label = QLabel("")
        connect_row.addWidget(self._connect_btn)
        connect_row.addWidget(self._connect_label)
        connect_row.addStretch()
        form.addRow(connect_row)

        self._model_combo = QComboBox()
        if cfg.get("ollama_model"):
            self._model_combo.addItem(cfg["ollama_model"])
        form.addRow("Model", self._model_combo)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self._cancel_btn = QPushButton("Cancel")
        self._save_btn = QPushButton("Save")
        btn_row.addStretch()
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

        self._connect_btn.clicked.connect(self._on_connect)
        self._cancel_btn.clicked.connect(self.reject)
        self._save_btn.clicked.connect(self._on_save)

    def _on_connect(self):
        self._connect_label.setText("")
        try:
            models = fetch_models(
                self._host_edit.text().strip(), self._port_spin.value()
            )
            self._model_combo.clear()
            self._model_combo.addItems(models)
            self._connect_label.setStyleSheet("color: green;")
            self._connect_label.setText(f"{len(models)} model(s) found")
        except Exception as e:
            self._connect_label.setStyleSheet("color: red;")
            self._connect_label.setText(f"Failed: {e}")

    def _on_save(self):
        self.settings_saved.emit({
            "ollama_enabled": self._enabled_check.isChecked(),
            "ollama_host": self._host_edit.text().strip(),
            "ollama_port": self._port_spin.value(),
            "ollama_model": self._model_combo.currentText(),
        })
        self.accept()
