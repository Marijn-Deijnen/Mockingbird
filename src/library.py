import json
from pathlib import Path

LIBRARY_PATH = Path(__file__).parent.parent / "output" / "library.json"


def load() -> list[dict]:
    if not LIBRARY_PATH.exists():
        return []
    try:
        with open(LIBRARY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save(entries: list[dict]) -> None:
    LIBRARY_PATH.parent.mkdir(exist_ok=True)
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_entry(entry: dict) -> list[dict]:
    entries = load()
    entries.insert(0, entry)
    save(entries)
    return entries


def update_filename(entry_id: str, new_filename: str) -> list[dict]:
    entries = load()
    for e in entries:
        if e["id"] == entry_id:
            e["filename"] = new_filename
            break
    save(entries)
    return entries


def delete_entry(entry_id: str) -> list[dict]:
    entries = [e for e in load() if e["id"] != entry_id]
    save(entries)
    return entries
