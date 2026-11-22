$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not on PATH."
    Write-Host "Install Python 3.10+ and run this script again."
    Read-Host "Press Enter to close"
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    py -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install PySide6 matplotlib qt-material pyinstaller

python -m PyInstaller --noconsole --onedir --name GermanFlashcardApp Flashcard.py

Write-Host ""
Write-Host "Build complete."
Write-Host "Output folder: $scriptDir\dist\GermanFlashcardApp"
Read-Host "Press Enter to close"
