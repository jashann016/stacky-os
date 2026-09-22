#!/usr/bin/env bash
set -e

PLIST_NAME="com.stacky.daily_sync.plist"
TARGET_PLIST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

echo "================================================================"
echo "    STACKY AI // UNINSTALL 11:45 AUTO-SYNC SCHEDULE             "
echo "================================================================"

if launchctl list | grep -q "com.stacky.daily_sync"; then
    echo "[*] Unloading calendar schedule from launchd..."
    launchctl unload "${TARGET_PLIST}" 2>/dev/null || true
fi

if [ -f "${TARGET_PLIST}" ]; then
    echo "[*] Removing plist from LaunchAgents..."
    rm -f "${TARGET_PLIST}"
fi

echo "[✓] 11:45 schedule removed completely from your Mac."
echo "================================================================"
