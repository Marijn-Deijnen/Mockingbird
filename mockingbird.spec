# mockingbird.spec — PyInstaller build spec for Mockingbird
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

datas = [
    ("src/assets", "assets"),              # style.qss + icon.png
]
datas += collect_data_files("imageio_ffmpeg")   # bundled ffmpeg binary
datas += collect_data_files("soundfile")         # libsndfile

# Explicitly bundle Python runtime DLLs — PyInstaller sometimes misses these
_py_dir = os.path.dirname(sys.executable)
binaries = [
    (dll, ".")
    for dll in glob.glob(os.path.join(_py_dir, "python*.dll"))
    + glob.glob(os.path.join(_py_dir, "vcruntime*.dll"))
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "soundfile",
        "imageio_ffmpeg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mockingbird",
    debug=False,
    strip=False,
    upx=False,
    console=False,          # no black console window
    icon="src/assets/icon.png",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Mockingbird",     # output folder: dist/Mockingbird/
)
