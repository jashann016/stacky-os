#!/usr/bin/env bash
set -e

PLIST_NAME="com.stacky.daemon.plist"
DEST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "======================================================="
echo "   UNINSTALLING STACKY AI BACKGROUND DAEMON SERVICE    "
echo "======================================================="

if [ -f "$DEST_PATH" ]; then
    echo "[+] Unloading service..."
    launchctl unload "$DEST_PATH" 2>/dev/null || true
    echo "[+] Removing plist from LaunchAgents..."
    rm -f "$DEST_PATH"
fi

PID_FILE="/Users/jashanpreetsingh/Downloads/Stacky Ai /stacky_daemon.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill -9 "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
fi

echo "[+] Stacky Daemon service uninstalled and stopped."
