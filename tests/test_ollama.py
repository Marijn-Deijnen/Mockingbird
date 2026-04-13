import pytest
import requests as req
from unittest.mock import patch, MagicMock


def test_fetch_models_returns_names():
    from src.ollama import fetch_models
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "models": [{"name": "gemma4:latest"}, {"name": "llama3:latest"}]
    }
    with patch("src.ollama.requests.get", return_value=mock_resp):
        result = fetch_models("127.0.0.1", 11434)
    assert result == ["gemma4:latest", "llama3:latest"]


def test_fetch_models_empty_list():
    from src.ollama import fetch_models
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"models": []}
    with patch("src.ollama.requests.get", return_value=mock_resp):
        result = fetch_models("127.0.0.1", 11434)
    assert result == []


def test_fetch_models_raises_on_connection_error():
    from src.ollama import fetch_models
    with patch("src.ollama.requests.get", side_effect=req.RequestException("refused")):
        with pytest.raises(req.RequestException):
            fetch_models("127.0.0.1", 11434)


def test_ollama_worker_attributes():
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import OllamaWorker
    w = OllamaWorker("hello", "127.0.0.1", 11434, "gemma4")
    assert w.text == "hello"
    assert w.host == "127.0.0.1"
    assert w.port == 11434
    assert w.model == "gemma4"


def test_naming_worker_attributes():
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import NamingWorker
    w = NamingWorker("hello world", "127.0.0.1", 11434, "gemma4")
    assert w.text == "hello world"
    assert w.host == "127.0.0.1"
    assert w.port == 11434
    assert w.model == "gemma4"


def test_naming_worker_emits_sanitized_name():
    import sys
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import patch, MagicMock
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import NamingWorker

    received = []
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Hello World! Title"}
    with patch("src.ollama.requests.post", return_value=mock_resp):
        w = NamingWorker("some text", "127.0.0.1", 11434, "gemma4")
        w.finished.connect(lambda name: received.append(name))
        w.run()
    assert received == ["hello_world_title"]


def test_naming_worker_silent_on_error():
    import sys
    import requests as req
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import patch
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import NamingWorker

    received = []
    with patch("src.ollama.requests.post", side_effect=req.RequestException("refused")):
        w = NamingWorker("some text", "127.0.0.1", 11434, "gemma4")
        w.finished.connect(lambda name: received.append(name))
        w.run()
    assert received == []


def test_ollama_worker_sends_system_prompt():
    import sys
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import patch, MagicMock
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import OllamaWorker

    captured = {}
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "ok"}

    def capture(url, json, timeout):
        captured.update(json)
        return mock_resp

    with patch("src.ollama.requests.post", side_effect=capture):
        w = OllamaWorker("hello", "127.0.0.1", 11434, "gemma4", system="Be brief.")
        w.run()

    assert captured.get("system") == "Be brief."


def test_ollama_worker_omits_system_when_empty():
    import sys
    from PyQt6.QtWidgets import QApplication
    from unittest.mock import patch, MagicMock
    app = QApplication.instance() or QApplication(sys.argv)
    from src.ollama import OllamaWorker

    captured = {}
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "ok"}

    def capture(url, json, timeout):
        captured.update(json)
        return mock_resp

    with patch("src.ollama.requests.post", side_effect=capture):
        w = OllamaWorker("hello", "127.0.0.1", 11434, "gemma4")
        w.run()

    assert "system" not in captured
