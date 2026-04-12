from datetime import datetime
from pathlib import Path

import soundfile as sf
from PyQt6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src import audio, config, library
from src.dialogs.settings_dialog import SettingsDialog
from src.model import GenerationWorker
from src.ollama import NamingWorker
from src.widgets.ai_panel import AIPanel
from src.widgets.library_panel import LibraryPanel
from src.widgets.nav_bar import NavBar
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
        self._naming_worker: NamingWorker | None = None
        self._current_output_path: str | None = None
        self._current_output_id: str | None = None
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
        outer_layout = QVBoxLayout(central)
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self._nav_bar = NavBar()
        outer_layout.addWidget(self._nav_bar)

        self._stack = QStackedWidget()
        outer_layout.addWidget(self._stack)

        # Page 0: Generate view
        generate_page = QWidget()
        gen_layout = QVBoxLayout(generate_page)
        gen_layout.setSpacing(0)
        gen_layout.setContentsMargins(14, 0, 14, 14)

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

        gen_layout.addWidget(self._ref_panel)
        gen_layout.addWidget(self._ai_panel)
        gen_layout.addWidget(self._text_panel)
        gen_layout.addWidget(self._settings_panel)
        gen_layout.addWidget(self._output_panel)
        self._stack.addWidget(generate_page)

        # Page 1: Library view
        self._library_panel = LibraryPanel()
        self._library_panel.load_entries(library.load())
        self._stack.addWidget(self._library_panel)

        # Wiring
        self._nav_bar.view_changed.connect(self._stack.setCurrentIndex)
        self._ref_panel.reference_changed.connect(self._on_reference_changed)
        self._ai_panel.result_ready.connect(self._text_panel.set_text)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)
        self._output_panel.generate_requested.connect(self._on_generate)
        self._output_panel.file_renamed.connect(self._on_file_renamed)
        self._library_panel.entry_deleted.connect(self._on_library_entry_deleted)
        self._library_panel.file_renamed.connect(self._on_file_renamed)

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

        profile = self._cfg["voice_profiles"].get(path)
        if profile:
            self._settings_panel.set_values(
                profile["cfg_value"],
                profile["inference_timesteps"],
                profile["use_denoiser"],
            )
        else:
            self._settings_panel.set_values(2.0, 10, False)

    def _on_settings_changed(self, values: dict):
        self._cfg.update(values)
        current_voice = self._ref_panel.current_path()
        if current_voice:
            self._cfg["voice_profiles"][current_voice] = {
                "cfg_value": values["cfg_value"],
                "inference_timesteps": values["inference_timesteps"],
                "use_denoiser": values["use_denoiser"],
            }
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

        self._current_output_path = out_path
        self._current_output_id = Path(out_path).stem

        text = self._text_panel.text()
        ref_path = self._ref_panel.current_path()

        entry = {
            "id": self._current_output_id,
            "filename": Path(out_path).name,
            "voice_path": ref_path or "",
            "text": text,
            "settings": self._settings_panel.values(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        entries = library.add_entry(entry)
        self._library_panel.load_entries(entries)
        self._output_panel.set_output(out_path)

        if self._cfg.get("ollama_enabled") and self._cfg.get("ollama_model"):
            self._naming_worker = NamingWorker(
                text=text,
                host=self._cfg["ollama_host"],
                port=self._cfg["ollama_port"],
                model=self._cfg["ollama_model"],
            )
            self._naming_worker.finished.connect(self._on_name_suggested)
            self._naming_worker.start()

    def _on_name_suggested(self, name: str):
        self._naming_worker.wait()
        if self._current_output_path:
            self._on_file_renamed(self._current_output_path, name)
        else:
            self._output_panel.set_filename(name)

    def _on_file_renamed(self, old_path: str, new_name: str):
        try:
            new_path = audio.rename_output(old_path, new_name)
        except Exception as e:
            self._output_panel.show_error(f"Failed to rename file:\n{e}")
            return
        if new_path == old_path:
            return
        self._current_output_path = new_path
        entries = library.update_filename(
            self._current_output_id, Path(new_path).name
        )
        self._library_panel.load_entries(entries)
        self._output_panel.update_output_path(new_path)

    def _on_library_entry_deleted(self, entry_id: str):
        entries = library.load()
        entry = next((e for e in entries if e["id"] == entry_id), None)
        if entry:
            file_path = audio.OUTPUT_DIR / entry["filename"]
            if file_path.exists():
                file_path.unlink()
        entries = library.delete_entry(entry_id)
        self._library_panel.load_entries(entries)
