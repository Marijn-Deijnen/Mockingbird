from PyQt6.QtCore import QThread, pyqtSignal


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
            from voxcpm import VoxCPM

            model = VoxCPM.from_pretrained(
                "openbmb/VoxCPM2", load_denoiser=self.use_denoiser
            )
            wav = model.generate(
                text=self.text,
                reference_wav_path=self.reference_wav,
                cfg_value=self.cfg_value,
                inference_timesteps=self.inference_timesteps,
            )
            self.finished.emit(wav, model.tts_model.sample_rate)
        except Exception as e:
            self.error.emit(str(e))
