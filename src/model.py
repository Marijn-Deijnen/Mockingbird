import threading

from PyQt6.QtCore import QThread, pyqtSignal

_cached_model = None
_cached_denoiser: bool | None = None
_model_lock = threading.Lock()


def _get_model(use_denoiser: bool):
    global _cached_model, _cached_denoiser
    with _model_lock:
        if _cached_model is None or _cached_denoiser != use_denoiser:
            from voxcpm import VoxCPM
            _cached_model = VoxCPM.from_pretrained(
                "openbmb/VoxCPM2", load_denoiser=use_denoiser
            )
            _cached_denoiser = use_denoiser
        return _cached_model


def preload_model(use_denoiser: bool) -> None:
    """Load the model in a background daemon thread so it is warm on first use."""
    threading.Thread(
        target=_get_model, args=(use_denoiser,), daemon=True, name="model-preload"
    ).start()


class GenerationWorker(QThread):
    finished = pyqtSignal(object, int)  # (wav ndarray, sample_rate)
    error = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        reference_wav: str,
        cfg_value: float,
        inference_timesteps: int,
        use_denoiser: bool,
    ):
        super().__init__()
        self.text = text
        self.reference_wav = reference_wav
        self.cfg_value = cfg_value
        self.inference_timesteps = inference_timesteps
        self.use_denoiser = use_denoiser

    def run(self):
        try:
            model = _get_model(self.use_denoiser)
            wav = model.generate(
                text=self.text,
                reference_wav_path=self.reference_wav,
                cfg_value=self.cfg_value,
                inference_timesteps=self.inference_timesteps,
            )
            self.finished.emit(wav, model.tts_model.sample_rate)
        except Exception as e:
            self.error.emit(str(e))
