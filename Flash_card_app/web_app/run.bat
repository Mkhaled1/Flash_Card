@echo off
REM Quick launcher script for German Flashcard Web App
REM Run this to start both backend and frontend servers

echo Starting German Flashcard Web App...
echo.

REM Start backend
echo Starting Flask Backend on http://localhost:5000...
start cmd /k "cd backend && pip install -r requirements.txt & python run.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Start frontend
echo Starting Frontend on http://localhost:8000...
start cmd /k "cd frontend && python -m http.server 8000"

timeout /t 2 /nobreak

REM Open browser
echo.
echo Opening browser...
start http://localhost:8000

echo.
echo Both servers are running!
echo - Backend: http://localhost:5000
echo - Frontend: http://localhost:8000
echo.
echo Close the command windows to shut down the servers.
