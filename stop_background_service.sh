#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PID_FILE="$DIR/stacky_daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "[+] Stacky AI background daemon (PID: $PID) stopped."
        osascript -e 'display notification "Stacky AI background daemon has been stopped." with title "Stacky AI" subtitle "Offline"' 2>/dev/null
        exit 0
    else
        rm -f "$PID_FILE"
        echo "[*] Stale PID file removed. Stacky was not running."
        exit 0
    fi
fi

pkill -f "stacky_daemon.py" 2>/dev/null
echo "[+] Stopped any running stacky_daemon processes."
