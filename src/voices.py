import json
from pathlib import Path

from src.paths import app_dir

VOICES_DIR = app_dir() / "audio"
VOICES_PATH = VOICES_DIR / "voices.json"


def load() -> list[dict]:
    if not VOICES_PATH.exists():
        return []
    try:
        with open(VOICES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save(entries: list[dict]) -> None:
    VOICES_PATH.parent.mkdir(exist_ok=True)
    with open(VOICES_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_voice(entry: dict) -> list[dict]:
    entries = load()
    entries.insert(0, entry)
    save(entries)
    return entries


def rename_voice(voice_id: str, display_name: str) -> list[dict]:
    entries = load()
    for e in entries:
        if e["id"] == voice_id:
            e["display_name"] = display_name
            break
    save(entries)
    return entries


def delete_voice(voice_id: str) -> list[dict]:
    entries = [e for e in load() if e["id"] != voice_id]
    save(entries)
    return entries
