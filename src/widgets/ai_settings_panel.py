from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ollama import fetch_models
from src.widgets.toggle_switch import ToggleSwitch


class AISettingsPanel(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._setup_ui(cfg)

    def _setup_ui(self, cfg: dict):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(12)

        # --- AI Prompt visibility ---
        prompt_group = QGroupBox("Generate Tab")
        prompt_form = QFormLayout(prompt_group)
        self._show_prompt_toggle = ToggleSwitch()
        self._show_prompt_toggle.setChecked(cfg.get("show_ai_prompt", True))
        prompt_form.addRow("Show AI Prompt panel", self._show_prompt_toggle)
        outer.addWidget(prompt_group)

        # --- Ollama connection ---
        ollama_group = QGroupBox("AI Assistant (Ollama)")
        form = QFormLayout(ollama_group)

        self._enabled_toggle = ToggleSwitch()
        self._enabled_toggle.setChecked(cfg.get("ollama_enabled", False))
        form.addRow("Enable AI features", self._enabled_toggle)

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

        outer.addWidget(ollama_group)
        outer.addStretch()

        self._connect_btn.clicked.connect(self._on_connect)
        self._show_prompt_toggle.toggled.connect(self._emit)
        self._enabled_toggle.toggled.connect(self._emit)
        self._host_edit.editingFinished.connect(self._emit)
        self._port_spin.valueChanged.connect(self._emit)
        self._model_combo.currentTextChanged.connect(self._emit)

    def values(self) -> dict:
        return {
            "ollama_enabled": self._enabled_toggle.isChecked(),
            "ollama_host": self._host_edit.text().strip(),
            "ollama_port": self._port_spin.value(),
            "ollama_model": self._model_combo.currentText(),
            "show_ai_prompt": self._show_prompt_toggle.isChecked(),
        }

    def _emit(self, _=None):
        self.settings_changed.emit(self.values())

    def _on_connect(self):
        self._connect_label.setText("")
        try:
            models = fetch_models(
                self._host_edit.text().strip(), self._port_spin.value()
            )
            self._model_combo.clear()
            self._model_combo.addItems(models)
            self._connect_label.setStyleSheet("color: #6ec97e;")
            self._connect_label.setText(f"{len(models)} model(s) found")
        except Exception as e:
            self._connect_label.setStyleSheet("color: #e05c5c;")
            self._connect_label.setText(f"Failed: {e}")
