#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PID_FILE="$DIR/stacky_daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "========================================="
        echo "  STACKY AI BACKGROUND DAEMON STATUS"
        echo "========================================="
        echo "[●] Status: ACTIVE & RUNNING (PID: $PID)"
        echo "[●] Mode: 100% Background (Zero Windows)"
        echo "[●] Recent Activity:"
        tail -n 8 "$DIR/stacky_daemon.log"
        exit 0
    fi
fi

echo "[○] Stacky AI is currently stopped / offline."
