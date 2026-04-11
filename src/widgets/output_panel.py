from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class OutputPanel(QGroupBox):
    generate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Output", parent)
        self._last_output: str | None = None
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._setup_ui()
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

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
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._generate_btn.clicked.connect(self.generate_requested)
        self._play_btn.clicked.connect(self._play)
        self._stop_btn.clicked.connect(self._stop)

    def set_generating(self, generating: bool):
        self._generate_btn.setEnabled(not generating)
        self._progress.setVisible(generating)
        if generating:
            self._status_label.setText("Generating...")

    def set_output(self, path: str):
        self._last_output = path
        self._status_label.setText(path)
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._play_btn.setEnabled(True)

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
