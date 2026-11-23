#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

python3 -m pip install -r "$REPO_ROOT/requirements.txt"

cd "$SCRIPT_DIR/backend"
python3 run.py &
SERVER_PID=$!

sleep 2
if command -v open >/dev/null 2>&1; then
    open http://localhost:5000
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5000
fi

wait "$SERVER_PID"
