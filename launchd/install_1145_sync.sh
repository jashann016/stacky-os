#!/usr/bin/env bash
set -e

PLIST_NAME="com.stacky.daily_sync.plist"
SOURCE_PLIST="$(cd "$(dirname "$0")" && pwd)/${PLIST_NAME}"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/${PLIST_NAME}"

echo "================================================================"
echo "    STACKY AI // INSTALL ZERO-FOOTPRINT 11:45 AUTO-SYNC         "
echo "================================================================"

mkdir -p "${TARGET_DIR}"

if launchctl list | grep -q "com.stacky.daily_sync"; then
    echo "[*] Unloading previous version of schedule..."
    launchctl unload "${TARGET_PLIST}" 2>/dev/null || true
fi

echo "[+] Copying plist to user LaunchAgents..."
cp "${SOURCE_PLIST}" "${TARGET_PLIST}"

echo "[+] Registering macOS kernel calendar trigger (11:45 AM & 11:45 PM)..."
launchctl load "${TARGET_PLIST}"

echo "----------------------------------------------------------------"
echo "[✓] Schedule successfully registered with macOS system timer!"
echo "[✓] Zero RAM and Zero CPU footprint: Nothing runs until 11:45."
echo "[✓] At 11:45, macOS wakes the script for 2 seconds to send today's files and exits."
echo "================================================================"
