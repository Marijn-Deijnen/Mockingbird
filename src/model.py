from PyQt6.QtCore import QThread, pyqtSignal

_cached_model = None
_cached_denoiser: bool | None = None


def _get_model(use_denoiser: bool):
    global _cached_model, _cached_denoiser
    if _cached_model is None or _cached_denoiser != use_denoiser:
        from voxcpm import VoxCPM
        _cached_model = VoxCPM.from_pretrained(
            "openbmb/VoxCPM2", load_denoiser=use_denoiser
        )
        _cached_denoiser = use_denoiser
    return _cached_model


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
