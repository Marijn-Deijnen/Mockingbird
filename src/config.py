import json
from pathlib import Path

from src.paths import app_dir

CONFIG_PATH = app_dir() / "config.json"

DEFAULTS = {
    "last_voice_id": "",
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "use_denoiser": False,
    "ollama_enabled": False,
    "ollama_host": "127.0.0.1",
    "ollama_port": 11434,
    "ollama_model": "",
    "show_ai_prompt": True,
    "voice_profiles": {},
    "style_prefix": "",
    "auto_play": False,
    "ai_system_prompt": (
        'You are a TTS assistant. Rewrite the user\'s input as natural spoken text '
        'for a voice called "{voice_name}". Return only the words to be spoken.'
    ),
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
