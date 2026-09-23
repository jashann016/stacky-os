#!/bin/bash
set -e

PLIST_NOTCH="$HOME/Library/LaunchAgents/com.stacky.notchbar.plist"
PLIST_TG="$HOME/Library/LaunchAgents/com.stacky.telegram.plist"

if [ -f "$PLIST_NOTCH" ]; then
    launchctl unload "$PLIST_NOTCH" 2>/dev/null || true
    rm -f "$PLIST_NOTCH"
    echo "[+] Stacky Notch Bar daemon uninstalled."
fi

if [ -f "$PLIST_TG" ]; then
    launchctl unload "$PLIST_TG" 2>/dev/null || true
    rm -f "$PLIST_TG"
    echo "[+] Stacky Telegram Bridge daemon uninstalled."
fi

# Kill any running Stacky background instances
killall stacky_notch_bar 2>/dev/null || true
pkill -f "launch_telegram_bridge.py" 2>/dev/null || true
echo "[+] All Stacky background services stopped cleanly."
