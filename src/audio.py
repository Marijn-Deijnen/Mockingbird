import re
import subprocess
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def ensure_wav(path: str) -> str:
    """Return a .wav path for the given audio file, converting from mp3 if needed."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if p.suffix.lower() == ".wav":
        return str(p)
    wav_path = p.with_suffix(".wav")
    if not wav_path.exists():
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-i", str(p), str(wav_path)], check=True)
    return str(wav_path)


def output_path() -> str:
    """Return a timestamped output path, creating the output directory if needed."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    return str(OUTPUT_DIR / f"{timestamp}.wav")


def rename_output(old_path: str, new_name: str) -> str:
    """Rename an output file to new_name (no extension). Returns new absolute path."""
    old = Path(old_path)
    safe = re.sub(r'[<>:"/\\|?*]', "", new_name).strip()
    if not safe:
        return old_path
    candidate = old.parent / f"{safe}.wav"
    counter = 2
    while candidate.exists() and candidate != old:
        candidate = old.parent / f"{safe}_{counter}.wav"
        counter += 1
    old.rename(candidate)
    return str(candidate)
