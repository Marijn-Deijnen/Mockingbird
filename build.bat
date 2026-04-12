@echo off
echo Installing PyInstaller...
pip install pyinstaller --quiet

echo.
echo Building Mockingbird...
pyinstaller mockingbird.spec --clean --noconfirm

echo.
echo Build complete.
echo Output: dist\Mockingbird\Mockingbird.exe
pause
