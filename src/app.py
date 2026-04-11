import soundfile as sf
from PyQt6.QtWidgets import QMainWindow, QMenuBar, QVBoxLayout, QWidget

from src import audio, config
from src.dialogs.settings_dialog import SettingsDialog
from src.model import GenerationWorker
from src.widgets.ai_panel import AIPanel
from src.widgets.output_panel import OutputPanel
from src.widgets.reference_panel import ReferencePanel
from src.widgets.settings_panel import SettingsPanel
from src.widgets.text_panel import TextPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mockingbird")
        self.setMinimumWidth(620)
        self._cfg = config.load()
        self._worker: GenerationWorker | None = None
        self._setup_menu()
        self._setup_ui()

    def _setup_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        settings_menu = menu_bar.addMenu("Settings")
        ai_action = settings_menu.addAction("AI Settings...")
        ai_action.triggered.connect(self._open_settings_dialog)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        self._ref_panel = ReferencePanel(self._cfg)
        self._ai_panel = AIPanel(
            host=self._cfg.get("ollama_host", "127.0.0.1"),
            port=self._cfg.get("ollama_port", 11434),
            model=self._cfg.get("ollama_model", ""),
        )
        self._ai_panel.setVisible(self._cfg.get("ollama_enabled", False))
        self._text_panel = TextPanel()
        self._settings_panel = SettingsPanel(self._cfg)
        self._output_panel = OutputPanel()

        layout.addWidget(self._ref_panel)
        layout.addWidget(self._ai_panel)
        layout.addWidget(self._text_panel)
        layout.addWidget(self._settings_panel)
        layout.addWidget(self._output_panel)

        self._ref_panel.reference_changed.connect(self._on_reference_changed)
        self._ai_panel.result_ready.connect(self._text_panel.set_text)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)
        self._output_panel.generate_requested.connect(self._on_generate)

    def _open_settings_dialog(self):
        dialog = SettingsDialog(self._cfg, parent=self)
        dialog.settings_saved.connect(self._on_ai_settings_saved)
        dialog.exec()

    def _on_ai_settings_saved(self, values: dict):
        self._cfg.update(values)
        config.save(self._cfg)
        self._ai_panel.setVisible(self._cfg["ollama_enabled"])
        self._ai_panel.update_config(
            self._cfg["ollama_host"],
            self._cfg["ollama_port"],
            self._cfg["ollama_model"],
        )

    def _on_reference_changed(self, path: str):
        self._cfg = config.add_recent_reference(self._cfg, path)
        config.save(self._cfg)
        self._ref_panel.update_recents(self._cfg)

    def _on_settings_changed(self, values: dict):
        self._cfg.update(values)
        config.save(self._cfg)

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            if not self._worker.wait(3000):
                self._worker.terminate()
        super().closeEvent(event)

    def _on_generate(self):
        if self._worker is not None and self._worker.isRunning():
            return

        ref_path = self._ref_panel.current_path()
        text = self._text_panel.text()

        if not ref_path:
            self._output_panel.show_warning("Please select a reference audio file.")
            return
        if not text:
            self._output_panel.show_warning("Please enter text to speak.")
            return

        try:
            wav_ref = audio.ensure_wav(ref_path)
        except Exception as e:
            self._output_panel.show_error(f"Failed to convert reference audio:\n{e}")
            return

        self._output_panel.set_generating(True)
        self._worker = GenerationWorker(
            text=text,
            reference_wav=wav_ref,
            cfg_value=self._cfg["cfg_value"],
            inference_timesteps=self._cfg["inference_timesteps"],
            use_denoiser=self._cfg["use_denoiser"],
        )
        self._worker.finished.connect(self._on_generation_done)
        self._worker.error.connect(self._output_panel.show_error)
        self._worker.start()

    def _on_generation_done(self, wav, sample_rate: int):
        try:
            out_path = audio.output_path()
            sf.write(out_path, wav, sample_rate)
        except Exception as e:
            self._output_panel.show_error(f"Failed to save output file:\n{e}")
            return
        self._output_panel.set_output(out_path)
