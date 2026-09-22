#!/bin/bash
set -e

PLIST_FILE="$HOME/Library/LaunchAgents/com.stacky.notchbar.plist"

if [ -f "$PLIST_FILE" ]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    rm -f "$PLIST_FILE"
    echo "[+] Stacky Notch Bar LaunchAgent daemon uninstalled successfully."
else
    echo "[!] No daemon plist found at $PLIST_FILE."
fi

# Kill any running notch bar instances
killall stacky_notch_bar 2>/dev/null || true
echo "[+] Process stopped."
