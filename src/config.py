import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULTS = {
    "last_reference": "",
    "recent_references": [],
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "use_denoiser": False,
    "ollama_enabled": False,
    "ollama_host": "127.0.0.1",
    "ollama_port": 11434,
    "ollama_model": "",
    "voice_profiles": {},
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()
    return {**DEFAULTS, **data}


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def add_recent_reference(cfg: dict, path: str) -> dict:
    recents = [p for p in cfg["recent_references"] if p != path]
    recents.insert(0, path)
    cfg = dict(cfg)
    cfg["recent_references"] = recents[:10]
    cfg["last_reference"] = path
    return cfg
