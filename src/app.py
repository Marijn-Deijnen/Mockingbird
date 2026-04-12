from datetime import datetime
from pathlib import Path

import soundfile as sf
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src import audio, config, library, voices
from src.model import GenerationWorker, preload_model
from src.ollama import NamingWorker
from src.widgets.ai_panel import AIPanel
from src.widgets.ai_settings_panel import AISettingsPanel
from src.widgets.library_panel import LibraryPanel
from src.widgets.voices_panel import VoicesPanel
from src.widgets.nav_bar import NavBar
from src.widgets.output_panel import OutputPanel
from src.widgets.settings_panel import SettingsPanel
from src.widgets.text_panel import TextPanel
from src.widgets.voice_selector import VoiceSelector


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mockingbird")
        self.setMinimumWidth(760)
        self._cfg = config.load()
        self._worker: GenerationWorker | None = None
        self._naming_worker: NamingWorker | None = None
        self._current_output_path: str | None = None
        self._current_output_id: str | None = None
        self._setup_ui()
        preload_model(self._cfg.get("use_denoiser", False))

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

        self._voice_selector = VoiceSelector()
        self._voice_selector.refresh(voices.load())
        if self._cfg.get("last_voice_id"):
            self._voice_selector.select_by_id(self._cfg["last_voice_id"])
        self._ai_panel = AIPanel(
            host=self._cfg.get("ollama_host", "127.0.0.1"),
            port=self._cfg.get("ollama_port", 11434),
            model=self._cfg.get("ollama_model", ""),
        )
        self._ai_panel.setVisible(
            self._cfg.get("ollama_enabled", False)
            and self._cfg.get("show_ai_prompt", True)
        )
        self._text_panel = TextPanel()
        self._settings_panel = SettingsPanel(self._cfg)
        self._output_panel = OutputPanel()

        gen_layout.addWidget(self._voice_selector)
        gen_layout.addWidget(self._ai_panel)
        gen_layout.addWidget(self._text_panel)
        gen_layout.addWidget(self._settings_panel)
        gen_layout.addWidget(self._output_panel)
        self._stack.addWidget(generate_page)

        # Page 1: Library view
        self._library_panel = LibraryPanel()
        self._library_panel.load_entries(library.load())
        self._stack.addWidget(self._library_panel)

        # Page 2: Voices view
        self._voices_panel = VoicesPanel()
        self._voices_panel.load_voices(voices.load())
        self._stack.addWidget(self._voices_panel)

        # Page 3: Settings view
        self._ai_settings_panel = AISettingsPanel(self._cfg)
        self._stack.addWidget(self._ai_settings_panel)

        # Wiring
        self._nav_bar.view_changed.connect(self._stack.setCurrentIndex)
        self._voice_selector.voice_changed.connect(self._on_voice_changed)
        self._voices_panel.voices_changed.connect(self._voice_selector.refresh)
        self._ai_panel.result_ready.connect(self._text_panel.set_text)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)
        self._output_panel.generate_requested.connect(self._on_generate)
        self._output_panel.file_renamed.connect(self._on_file_renamed)
        self._library_panel.entry_deleted.connect(self._on_library_entry_deleted)
        self._library_panel.file_renamed.connect(self._on_file_renamed)
        self._ai_settings_panel.settings_changed.connect(self._on_ai_settings_changed)

    def _on_ai_settings_changed(self, values: dict):
        self._cfg.update(values)
        config.save(self._cfg)
        self._ai_panel.setVisible(
            values["ollama_enabled"] and values["show_ai_prompt"]
        )
        self._ai_panel.update_config(
            values["ollama_host"],
            values["ollama_port"],
            values["ollama_model"],
        )

    def _on_voice_changed(self, voice_id: str, path: str) -> None:
        self._cfg["last_voice_id"] = voice_id
        config.save(self._cfg)
        profile = self._cfg["voice_profiles"].get(voice_id)
        if profile:
            self._settings_panel.set_values(
                profile["cfg_value"],
                profile["inference_timesteps"],
                profile["use_denoiser"],
            )
        else:
            self._settings_panel.set_values(2.0, 10, False)

    def _on_settings_changed(self, values: dict):
        prev_denoiser = self._cfg.get("use_denoiser", False)
        self._cfg.update(values)
        current_voice_id = self._voice_selector.current_voice_id()
        if current_voice_id:
            self._cfg["voice_profiles"][current_voice_id] = {
                "cfg_value": values["cfg_value"],
                "inference_timesteps": values["inference_timesteps"],
                "use_denoiser": values["use_denoiser"],
            }
        config.save(self._cfg)
        if values["use_denoiser"] != prev_denoiser:
            preload_model(values["use_denoiser"])

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            if not self._worker.wait(3000):
                self._worker.terminate()
        super().closeEvent(event)

    def _on_generate(self):
        if self._worker is not None and self._worker.isRunning():
            return

        ref_path = self._voice_selector.current_path()
        text = self._text_panel.text()

        if not ref_path:
            self._output_panel.show_warning("Please select a voice.")
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
        ref_path = self._voice_selector.current_path()

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
            Path(old_path).stem, Path(new_path).name
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
