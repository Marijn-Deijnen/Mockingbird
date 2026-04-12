"""
Central path resolution for both frozen (PyInstaller) and source-run modes.

  app_dir()    -- next to the .exe when frozen, project root otherwise.
                  Used for runtime data: config.json, output/, audio/
  assets_dir() -- _MEIPASS/assets/ when frozen, src/assets/ otherwise.
                  Used for read-only bundled files: style.qss, icon.png
"""
import sys
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets"
    return Path(__file__).parent / "assets"
