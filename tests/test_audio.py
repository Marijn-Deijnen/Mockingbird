import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def tmp_output(tmp_path, monkeypatch):
    import src.audio as audio_mod
    monkeypatch.setattr(audio_mod, "OUTPUT_DIR", tmp_path / "output")
    return tmp_path / "output"


def test_output_path_creates_directory(tmp_output):
    import src.audio as audio_mod
    path = audio_mod.output_path()
    assert tmp_output.exists()


def test_output_path_format(tmp_output):
    import src.audio as audio_mod
    path = audio_mod.output_path()
    filename = Path(path).name
    assert re.match(r"\d{4}-\d{2}-\d{2}_\d{6}_\d+\.wav", filename), f"Bad format: {filename}"


def test_ensure_wav_passthrough_for_wav(tmp_path):
    import src.audio as audio_mod
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"")
    result = audio_mod.ensure_wav(str(wav_file))
    assert result == str(wav_file)


def test_ensure_wav_converts_mp3(tmp_path):
    import src.audio as audio_mod
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"fake mp3")
    wav_expected = tmp_path / "test.wav"

    with patch("src.audio.subprocess.run") as mock_run, \
         patch("src.audio.imageio_ffmpeg.get_ffmpeg_exe", return_value="/usr/bin/ffmpeg"):
        mock_run.return_value = MagicMock(returncode=0)
        result = audio_mod.ensure_wav(str(mp3_file))

    assert result == str(wav_expected)
    mock_run.assert_called_once()


def test_ensure_wav_skips_conversion_if_wav_exists(tmp_path):
    import src.audio as audio_mod
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"fake mp3")
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"existing wav")

    with patch("src.audio.subprocess.run") as mock_run:
        result = audio_mod.ensure_wav(str(mp3_file))

    mock_run.assert_not_called()
    assert result == str(wav_file)
