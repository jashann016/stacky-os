#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BINARY="$DIR/bin/stacky_notch_bar"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.stacky.notchbar.plist"

if [ ! -f "$BINARY" ]; then
    echo "[+] Compiling binary first..."
    clang -O2 -fobjc-arc "$DIR/macos/notch_overlay.m" -framework Cocoa -framework WebKit -o "$BINARY"
fi

mkdir -p "$PLIST_DIR"

cat << EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.stacky.notchbar</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BINARY</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/stacky_notch.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/stacky_notch.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "================================================================="
echo "       STACKY NOTCH BAR AUTO-START DAEMON INSTALLED!             "
echo "================================================================="
echo "[+] Service Label : com.stacky.notchbar"
echo "[+] Plist Path    : $PLIST_FILE"
echo "[+] Status        : Active & running silently at 0.0% CPU."
echo "[+] WAKE KEY      : Double-tap [Control] (Ctrl + Ctrl)"
echo "[+] SLEEP KEY     : Press [Esc] or single [Control]"
echo "================================================================="
