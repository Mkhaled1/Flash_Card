@echo off
setlocal

echo Installing dependencies...
pushd "%~dp0..\.."
python -m pip install -r requirements.txt
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo Starting German Flashcard Web App...
start "German Flashcard App" cmd /k "pushd ""%~dp0backend"" && python run.py"
timeout /t 3 /nobreak >nul
start "" http://localhost:5000
