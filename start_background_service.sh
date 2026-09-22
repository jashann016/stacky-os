#!/bin/bash
# Start Stacky AI as a detached, silent macOS background process
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

LOG_FILE="$DIR/stacky_daemon.log"
PID_FILE="$DIR/stacky_daemon.pid"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[!] Stacky AI is already running in the background (PID: $OLD_PID)."
        exit 0
    fi
fi

echo "[*] Launching Stacky AI Core 100% in the background..."
nohup python3 stacky_daemon.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 1
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "[+] Stacky AI is now running silently in the background (PID: $NEW_PID)."
    echo "[+] Log file: $LOG_FILE"
    echo "[+] No windows, no browser popups, zero desktop clutter."
else
    echo "[-] Failed to start daemon. Check $LOG_FILE"
    exit 1
fi
