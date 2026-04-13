# mockingbird.spec — PyInstaller build spec for Mockingbird
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

datas = [
    ("src/assets", "assets"),              # style.qss + icon.png
]
datas += collect_data_files("imageio_ffmpeg")   # bundled ffmpeg binary
datas += collect_data_files("soundfile")         # libsndfile

# Collect voxcpm as source files on disk so TorchScript can call
# inspect.getsource() at runtime (compiling to .pyc breaks this)
voxcpm_datas, voxcpm_binaries, voxcpm_hiddenimports = collect_all("voxcpm")
datas += voxcpm_datas

# Explicitly bundle Python runtime DLLs — PyInstaller sometimes misses these.
# Use sys.base_prefix so this works correctly inside a venv too.
_base_dir = sys.base_prefix
binaries = [
    (dll, ".")
    for dll in glob.glob(os.path.join(_base_dir, "python*.dll"))
    + glob.glob(os.path.join(_base_dir, "vcruntime*.dll"))
]
binaries += voxcpm_binaries

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
        *voxcpm_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    cipher=block_cipher,
    noarchive=False,
)

# Remove voxcpm from the compiled PYZ archive so it stays as .py files
# on disk — required for TorchScript's inspect.getsource() to work
a.pure = [entry for entry in a.pure if not entry[0].startswith("voxcpm")]

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
