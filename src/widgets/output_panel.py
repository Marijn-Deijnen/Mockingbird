from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OutputPanel(QGroupBox):
    generate_requested = pyqtSignal()
    file_renamed = pyqtSignal(str, str)  # (old_path, new_name_without_ext)

    def __init__(self, parent=None):
        super().__init__("Output", parent)
        self._last_output: str | None = None
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._setup_ui()
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(
            lambda err, msg: self._status_label.setText(f"Playback error: {msg}")
        )

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._generate_btn = QPushButton("Generate")
        self._play_btn = QPushButton("▶ Play")
        self._stop_btn = QPushButton("■ Stop")
        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        btn_row.addWidget(self._generate_btn)
        btn_row.addWidget(self._play_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Filename row — hidden until first output
        self._filename_row_widget = QWidget()
        self._filename_row_widget.setVisible(False)
        filename_row_layout = QHBoxLayout(self._filename_row_widget)
        filename_row_layout.setContentsMargins(0, 0, 0, 0)
        filename_row_layout.addWidget(QLabel("File name:"))
        self._filename_edit_widget = QLineEdit()
        self._filename_edit_widget.setPlaceholderText("filename")
        filename_row_layout.addWidget(self._filename_edit_widget)
        layout.addWidget(self._filename_row_widget)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._generate_btn.clicked.connect(self.generate_requested)
        self._play_btn.clicked.connect(self._play)
        self._stop_btn.clicked.connect(self._stop)
        self._filename_edit_widget.editingFinished.connect(self._on_filename_edit_finished)

    def set_generating(self, generating: bool):
        self._generate_btn.setEnabled(not generating)
        self._progress.setVisible(generating)
        if generating:
            self._status_label.setText("Generating...")
        else:
            self._status_label.setText("")

    def set_output(self, path: str):
        self._last_output = path
        self._status_label.setText(path)
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._play_btn.setEnabled(True)
        self._filename_edit_widget.setText(Path(path).stem)
        self._filename_row_widget.setVisible(True)

    def set_filename(self, name: str) -> None:
        """Called externally (e.g. NamingWorker) to pre-fill the filename field."""
        self._filename_edit_widget.setText(name)

    def update_output_path(self, new_path: str) -> None:
        """Called after a successful rename to update stored path and field."""
        self._last_output = new_path
        self._status_label.setText(new_path)
        self._filename_edit_widget.setText(Path(new_path).stem)

    def show_error(self, message: str):
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText("Generation failed.")
        QMessageBox.critical(self, "Generation Failed", message)

    def show_warning(self, message: str):
        self._status_label.setText(message)

    def _play(self):
        if self._last_output:
            self._player.setSource(QUrl.fromLocalFile(self._last_output))
            self._player.play()
            self._stop_btn.setEnabled(True)

    def _stop(self):
        self._player.stop()

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._stop_btn.setEnabled(False)

    def _on_filename_edit_finished(self):
        new_name = self._filename_edit_widget.text().strip()
        if not new_name:
            if self._last_output:
                self._filename_edit_widget.setText(Path(self._last_output).stem)
            return
        if self._last_output and new_name != Path(self._last_output).stem:
            self.file_renamed.emit(self._last_output, new_name)
