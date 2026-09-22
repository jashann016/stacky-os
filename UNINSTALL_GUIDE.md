# 🛑 How to Disable or Completely Uninstall Stacky Notch Bar

If you ever want to turn off or completely remove the background service from your Mac at any time, run this single command in your Terminal:

```bash
cd "/Users/jashanpreetsingh/Downloads/Stacky Ai "
bash scripts/uninstall_notch_daemon.sh
```

---

### What this command does:
1. **Unloads the daemon:** Immediately deregisters `com.stacky.notchbar` from macOS.
2. **Deletes the LaunchAgent plist:** Removes `~/Library/LaunchAgents/com.stacky.notchbar.plist`.
3. **Kills the process:** Terminates any active notch overlay process immediately.
4. **Zero trace left:** Restores your Mac to 100% stock clean state as if it was never installed.

---

### How to re-enable it in the future (if you ever change your mind):
```bash
cd "/Users/jashanpreetsingh/Downloads/Stacky Ai "
bash scripts/install_notch_daemon.sh
```
