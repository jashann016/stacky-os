#!/usr/bin/env bash
set -e

PLIST_NAME="com.stacky.daemon.plist"
SRC_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$PLIST_NAME"
DEST_DIR="$HOME/Library/LaunchAgents"
DEST_PATH="$DEST_DIR/$PLIST_NAME"

echo "======================================================="
echo "   INSTALLING STACKY AI 24/7 BACKGROUND DAEMON SERVICE "
echo "======================================================="

mkdir -p "$DEST_DIR"

if launchctl list | grep -q "com.stacky.daemon"; then
    echo "[+] Unloading existing service instance..."
    launchctl unload "$DEST_PATH" 2>/dev/null || true
fi

echo "[+] Copying plist to $DEST_PATH..."
cp "$SRC_PATH" "$DEST_PATH"

echo "[+] Loading service via launchctl..."
launchctl load "$DEST_PATH"

echo "[+] Stacky Daemon successfully installed and armed!"
echo "[+] Status check: launchctl list | grep com.stacky.daemon"
echo "[+] Log file: tail -f '/Users/jashanpreetsingh/Downloads/Stacky Ai /stacky_daemon.log'"
