from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QWidget,
)


class SettingsPanel(QGroupBox):
    settings_changed = pyqtSignal(dict)

    def __init__(self, cfg: dict, parent=None):
        super().__init__("Voice Settings", parent)
        self._setup_ui(cfg)

    def _setup_ui(self, cfg: dict):
        layout = QFormLayout(self)

        # --- CFG Value ---
        cfg_widget = QWidget()
        cfg_row = QHBoxLayout(cfg_widget)
        cfg_row.setContentsMargins(0, 0, 0, 0)
        self._cfg_slider = QSlider(Qt.Orientation.Horizontal)
        self._cfg_slider.setRange(1, 100)  # 1 = 0.1, 100 = 10.0
        self._cfg_spin = QDoubleSpinBox()
        self._cfg_spin.setRange(0.1, 10.0)
        self._cfg_spin.setSingleStep(0.1)
        self._cfg_spin.setDecimals(1)
        self._cfg_spin.setFixedWidth(70)
        cfg_row.addWidget(self._cfg_slider)
        cfg_row.addWidget(self._cfg_spin)
        layout.addRow("CFG Value", cfg_widget)

        # --- Inference Steps ---
        steps_widget = QWidget()
        steps_row = QHBoxLayout(steps_widget)
        steps_row.setContentsMargins(0, 0, 0, 0)
        self._steps_slider = QSlider(Qt.Orientation.Horizontal)
        self._steps_slider.setRange(1, 100)
        self._steps_spin = QSpinBox()
        self._steps_spin.setRange(1, 100)
        self._steps_spin.setFixedWidth(70)
        steps_row.addWidget(self._steps_slider)
        steps_row.addWidget(self._steps_spin)
        layout.addRow("Inference Steps", steps_widget)

        # --- Denoiser ---
        denoiser_widget = QWidget()
        denoiser_row = QHBoxLayout(denoiser_widget)
        denoiser_row.setContentsMargins(0, 0, 0, 0)
        self._denoiser_check = QCheckBox()
        self._denoiser_check.setFixedWidth(18)
        denoiser_row.addWidget(self._denoiser_check)
        denoiser_row.addStretch()
        layout.addRow("Use Denoiser", denoiser_widget)

        # Set initial values (block signals to avoid spurious saves on startup)
        self._cfg_spin.blockSignals(True)
        self._cfg_slider.blockSignals(True)
        self._steps_spin.blockSignals(True)
        self._steps_slider.blockSignals(True)
        self._denoiser_check.blockSignals(True)

        self._cfg_spin.setValue(cfg.get("cfg_value", 2.0))
        self._cfg_slider.setValue(int(round(cfg.get("cfg_value", 2.0) * 10)))
        self._steps_spin.setValue(cfg.get("inference_timesteps", 10))
        self._steps_slider.setValue(cfg.get("inference_timesteps", 10))
        self._denoiser_check.setChecked(cfg.get("use_denoiser", False))

        self._cfg_spin.blockSignals(False)
        self._cfg_slider.blockSignals(False)
        self._steps_spin.blockSignals(False)
        self._steps_slider.blockSignals(False)
        self._denoiser_check.blockSignals(False)

        # Link slider <-> spinbox (bidirectional)
        self._cfg_slider.valueChanged.connect(
            lambda v: self._cfg_spin.setValue(round(v / 10, 1))
        )
        self._cfg_spin.valueChanged.connect(
            lambda v: self._cfg_slider.setValue(int(round(v * 10)))
        )
        self._steps_slider.valueChanged.connect(self._steps_spin.setValue)
        self._steps_spin.valueChanged.connect(self._steps_slider.setValue)

        # Emit settings_changed on any change
        self._cfg_spin.valueChanged.connect(self._emit)
        self._steps_spin.valueChanged.connect(self._emit)
        self._denoiser_check.toggled.connect(self._emit)

    def _emit(self, _=None):
        self.settings_changed.emit(self.values())

    def values(self) -> dict:
        return {
            "cfg_value": self._cfg_spin.value(),
            "inference_timesteps": self._steps_spin.value(),
            "use_denoiser": self._denoiser_check.isChecked(),
        }

    def set_values(self, cfg_value: float, inference_timesteps: int, use_denoiser: bool) -> None:
        self._cfg_spin.blockSignals(True)
        self._cfg_slider.blockSignals(True)
        self._steps_spin.blockSignals(True)
        self._steps_slider.blockSignals(True)
        self._denoiser_check.blockSignals(True)

        self._cfg_spin.setValue(cfg_value)
        self._cfg_slider.setValue(int(round(cfg_value * 10)))
        self._steps_spin.setValue(inference_timesteps)
        self._steps_slider.setValue(inference_timesteps)
        self._denoiser_check.setChecked(use_denoiser)

        self._cfg_spin.blockSignals(False)
        self._cfg_slider.blockSignals(False)
        self._steps_spin.blockSignals(False)
        self._steps_slider.blockSignals(False)
        self._denoiser_check.blockSignals(False)
