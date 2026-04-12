import os
import pytest

ENTRIES = [
    {
        "id": "1",
        "filename": "hello_world.wav",
        "voice_path": "voices/alice.wav",
        "text": "Hello world",
    },
    {
        "id": "2",
        "filename": "goodbye.wav",
        "voice_path": "voices/bob.wav",
        "text": "Goodbye friend",
    },
    {
        "id": "3",
        "filename": "alice_test.wav",
        "voice_path": "voices/alice.wav",
        "text": "Test phrase",
    },
]


def test_filter_no_constraints():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "Newest first")
    assert result == ENTRIES


def test_filter_by_voice():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "alice.wav", "Newest first")
    assert len(result) == 2
    assert all(os.path.basename(e["voice_path"]) == "alice.wav" for e in result)


def test_filter_by_search_filename():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "hello", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_filter_by_search_text():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "goodbye", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_filter_search_case_insensitive():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "HELLO", "All voices", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_sort_oldest_first():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "Oldest first")
    assert [e["id"] for e in result] == ["3", "2", "1"]


def test_sort_by_voice_az():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "", "All voices", "By voice A→Z")
    voices = [os.path.basename(e["voice_path"]) for e in result]
    assert voices == sorted(voices)


def test_filter_combined_voice_and_search():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "test", "alice.wav", "Newest first")
    assert len(result) == 1
    assert result[0]["id"] == "3"


def test_filter_no_match_returns_empty():
    from src.widgets.library_panel import filter_entries
    result = filter_entries(ENTRIES, "zzznomatch", "All voices", "Newest first")
    assert result == []
