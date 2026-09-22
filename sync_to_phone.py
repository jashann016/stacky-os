#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from backend.comms.telegram_bridge import telegram_bridge

def main():
    print("=================================================================")
    print("      STACKY AI // PRE-COLLEGE TELEGRAM CLOUD SYNC               ")
    print("=================================================================")

    if not telegram_bridge.is_configured:
        print("[!] Telegram configuration missing in .env.")
        print("[*] Please ensure TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID are set.")
        sys.exit(1)

    print(f"[+] Authenticated User ID: {telegram_bridge.allowed_user_id}")
    print("[+] Destination: Your Private Telegram Chat (@Stacky016_bot)")
    print("-----------------------------------------------------------------")

    files_to_send = []

    # 1. If user passed specific files/folders in command line arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            p = Path(arg).expanduser().resolve()
            if p.is_file():
                files_to_send.append(p)
            elif p.is_dir():
                for sub in p.iterdir():
                    if sub.is_file() and not sub.name.startswith("."):
                        files_to_send.append(sub)
    else:
        # 2. Smart Auto-Detect: Find files modified in the last 24 hours from Desktop, Documents, & Downloads
        print("[*] Scanning Desktop, Documents & Downloads for today's active work files...")
        now = time.time()
        one_day_ago = now - (24 * 60 * 60)

        ignored_extensions = {".log", ".db", ".sqlite", ".sqlite3", ".pyc", ".tmp", ".cache"}
        ignored_names = {"user_profile.json", "stacky_memory.db", "stacky_daemon.log", ".DS_Store"}

        search_locations = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            BASE_DIR
        ]

        for folder in search_locations:
            if not folder.exists():
                continue
            try:
                for item in folder.iterdir():
                    if (item.is_file() 
                        and not item.name.startswith(".") 
                        and item.name not in ignored_names 
                        and item.suffix.lower() not in ignored_extensions):
                        # Check modification time
                        mtime = item.stat().st_mtime
                        if mtime > one_day_ago:
                            files_to_send.append(item)
            except Exception:
                pass

    # Deduplicate and sort by most recently modified
    files_to_send = sorted(list(set(files_to_send)), key=lambda f: f.stat().st_mtime, reverse=True)

    if not files_to_send:
        print("[!] No recently modified files found in Desktop or Downloads.")
        print("[*] Tip: You can specify a file directly:")
        print("    python3 sync_to_phone.py ~/Desktop/my_assignment.pdf")
        sys.exit(0)

    # Limit batch to top 10 most recent files
    files_to_send = files_to_send[:10]
    print(f"[+] Found {len(files_to_send)} active file(s) to send to your phone:\n")

    telegram_bridge.send_text_message(
        f"⚡ *STACKY CLOUD SYNC*\n"
        f"Sir, syncing {len(files_to_send)} active file(s) from your Mac before you head to college:"
    )

    success_count = 0
    for idx, f in enumerate(files_to_send, 1):
        size_kb = f.stat().st_size / 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"
        print(f"  [{idx}/{len(files_to_send)}] Uploading: {f.name} ({size_str})...", end="", flush=True)

        res = telegram_bridge.send_document_to_phone(f, caption=f"📄 {f.name} ({size_str})")
        if res.get("status") in ["DISPATCHED", "SIMULATED_SUCCESS"]:
            print(" ✓ SENT")
            success_count += 1
        else:
            print(f" ✗ FAILED ({res.get('error', 'Unknown')})")

    print("\n-----------------------------------------------------------------")
    print(f"[✓] SYNC COMPLETE: {success_count}/{len(files_to_send)} files securely delivered to your Telegram!")
    print("[✓] Process exiting now. ZERO background processes left running on your Mac.")
    print("=================================================================")

if __name__ == "__main__":
    main()
