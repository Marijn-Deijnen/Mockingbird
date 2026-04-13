import re

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

    def __init__(self, text: str, host: str, port: int, model: str, system: str = ""):
        super().__init__()
        self.text = text
        self.host = host
        self.port = port
        self.model = model
        self.system = system

    def run(self):
        try:
            payload = {"model": self.model, "prompt": self.text, "stream": False}
            if self.system:
                payload["system"] = self.system
            response = requests.post(
                f"http://{self.host}:{self.port}/api/generate",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            self.finished.emit(response.json()["response"])
        except Exception as e:
            self.error.emit(str(e))


class NamingWorker(QThread):
    finished = pyqtSignal(str)  # sanitized suggested name, no extension

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
                json={
                    "model": self.model,
                    "prompt": (
                        "Give a title for this text, suitable as a filename. "
                        "Maximum 5 words. No punctuation, no quotes, no explanation. "
                        "Only the title words, nothing else. "
                        f"Text: {self.text}"
                    ),
                    "stream": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            raw = response.json()["response"].strip()
            name = re.sub(r"[^\w\s-]", "", raw).strip()
            words = name.split()[:5]
            name = "_".join(words).lower()
            if name:
                self.finished.emit(name)
        except Exception:
            return
