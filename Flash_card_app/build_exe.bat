@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not on PATH.
    echo Install Python 3.10+ and try again.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    py -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install PySide6 matplotlib qt-material pyinstaller

python -m PyInstaller --noconsole --onedir --name GermanFlashcardApp Flashcard.py

echo.
echo Build complete.
echo Output folder: %CD%\dist\GermanFlashcardApp
pause
