#!/bin/bash
# Quick launcher script for German Flashcard Web App
# Run: chmod +x run.sh && ./run.sh

echo "Starting German Flashcard Web App..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# Start backend
echo "Starting Flask Backend on http://localhost:5000..."
cd backend
pip install -r requirements.txt
python3 run.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start frontend
echo "Starting Frontend on http://localhost:8000..."
cd ../frontend
python3 -m http.server 8000 &
FRONTEND_PID=$!

sleep 2

# Open browser
echo ""
echo "Opening browser..."
if command -v open &> /dev/null; then
    open http://localhost:8000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000
fi

echo ""
echo "Both servers are running!"
echo "- Backend: http://localhost:5000"
echo "- Frontend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the servers"

# Wait for user interrupt
wait
