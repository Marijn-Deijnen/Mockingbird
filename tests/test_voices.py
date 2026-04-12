import pytest


@pytest.fixture
def tmp_voices(tmp_path, monkeypatch):
    import src.voices as voices_mod
    monkeypatch.setattr(voices_mod, "VOICES_PATH", tmp_path / "audio" / "voices.json")
    monkeypatch.setattr(voices_mod, "VOICES_DIR", tmp_path / "audio")
    return tmp_path / "audio" / "voices.json"


def test_load_returns_empty_when_no_file(tmp_voices):
    import src.voices as voices_mod
    assert voices_mod.load() == []


def test_load_returns_empty_on_corrupted_file(tmp_voices):
    import src.voices as voices_mod
    tmp_voices.parent.mkdir(parents=True, exist_ok=True)
    tmp_voices.write_bytes(b"not json{{")
    assert voices_mod.load() == []


def test_add_voice_prepends(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.add_voice({"id": "b", "filename": "b.wav", "display_name": "Bob"})
    entries = voices_mod.load()
    assert entries[0]["id"] == "b"
    assert entries[1]["id"] == "a"


def test_rename_voice(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.rename_voice("a", "Alicia")
    assert voices_mod.load()[0]["display_name"] == "Alicia"


def test_rename_unknown_id_is_noop(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.rename_voice("does-not-exist", "Bob")
    assert voices_mod.load()[0]["display_name"] == "Alice"


def test_delete_voice(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.add_voice({"id": "b", "filename": "b.wav", "display_name": "Bob"})
    voices_mod.delete_voice("a")
    entries = voices_mod.load()
    assert len(entries) == 1
    assert entries[0]["id"] == "b"


def test_delete_unknown_id_is_noop(tmp_voices):
    import src.voices as voices_mod
    voices_mod.add_voice({"id": "a", "filename": "a.wav", "display_name": "Alice"})
    voices_mod.delete_voice("does-not-exist")
    assert len(voices_mod.load()) == 1
