@echo off
setlocal
echo =============================================
echo  Mockingbird - CPU Release Build
echo =============================================
echo.

if not exist ".build-venv" (
    echo Creating build environment...
    python -m venv .build-venv
    if errorlevel 1 goto error

    echo.
    echo Installing CPU PyTorch ^(no CUDA^)...
    .build-venv\Scripts\pip install torch torchvision torchaudio --quiet
    if errorlevel 1 goto error

    echo Installing app dependencies...
    .build-venv\Scripts\pip install pyqt6 voxcpm soundfile requests imageio-ffmpeg pyinstaller --quiet
    if errorlevel 1 goto error
) else (
    echo Build environment already exists.
    echo Delete .build-venv to force a clean reinstall.
)

echo.
echo Building exe...
.build-venv\Scripts\pyinstaller mockingbird.spec --clean --noconfirm
if errorlevel 1 goto error

echo.
echo =============================================
echo  Build complete!
echo  Output: dist\Mockingbird\Mockingbird.exe
echo =============================================
goto end

:error
echo.
echo Build failed. Check the output above.

:end
pause
