import pytest


@pytest.fixture
def tmp_library(tmp_path, monkeypatch):
    import src.library as lib_mod
    monkeypatch.setattr(lib_mod, "LIBRARY_PATH", tmp_path / "output" / "library.json")
    return tmp_path / "output" / "library.json"


def test_load_returns_empty_when_no_file(tmp_library):
    import src.library as lib_mod
    assert lib_mod.load() == []


def test_load_returns_empty_on_corrupted_file(tmp_library):
    import src.library as lib_mod
    tmp_library.parent.mkdir(parents=True, exist_ok=True)
    tmp_library.write_bytes(b"not json{{")
    assert lib_mod.load() == []


def test_add_entry_prepends(tmp_library):
    import src.library as lib_mod
    lib_mod.add_entry({"id": "a", "filename": "a.wav"})
    lib_mod.add_entry({"id": "b", "filename": "b.wav"})
    entries = lib_mod.load()
    assert entries[0]["id"] == "b"
    assert entries[1]["id"] == "a"


def test_update_filename(tmp_library):
    import src.library as lib_mod
    lib_mod.add_entry({"id": "a", "filename": "old.wav"})
    lib_mod.update_filename("a", "new.wav")
    assert lib_mod.load()[0]["filename"] == "new.wav"


def test_delete_entry(tmp_library):
    import src.library as lib_mod
    lib_mod.add_entry({"id": "a", "filename": "a.wav"})
    lib_mod.add_entry({"id": "b", "filename": "b.wav"})
    lib_mod.delete_entry("a")
    entries = lib_mod.load()
    assert len(entries) == 1
    assert entries[0]["id"] == "b"


def test_update_filename_unknown_id_is_noop(tmp_library):
    import src.library as lib_mod
    lib_mod.add_entry({"id": "a", "filename": "a.wav"})
    lib_mod.update_filename("does-not-exist", "x.wav")
    assert lib_mod.load()[0]["filename"] == "a.wav"
