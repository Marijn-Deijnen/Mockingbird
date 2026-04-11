import requests
from PyQt6.QtCore import QThread, pyqtSignal


def fetch_models(host: str, port: int) -> list[str]:
    response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
    response.raise_for_status()
    data = response.json()
    return [m["name"] for m in data.get("models", [])]


class OllamaWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text: str, host: str, port: int, model: str):
        super().__init__()
        self.text = text
        self.host = host
        self.port = port
        self.model = model

    def run(self):
        try:
            response = requests.post(
                f"http://{self.host}:{self.port}/api/generate",
                json={"model": self.model, "prompt": self.text, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            self.finished.emit(response.json()["response"])
        except Exception as e:
            self.error.emit(str(e))
