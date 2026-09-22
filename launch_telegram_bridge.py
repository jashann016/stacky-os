#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip()

print("=================================================================")
print("        STACKY AI // TELEGRAM REMOTE PHONE BRIDGE                ")
print("=================================================================")

if not BOT_TOKEN:
    print("\n[!] TELEGRAM BOT TOKEN MISSING IN .env")
    print("-----------------------------------------------------------------")
    print("1. Open Telegram and message: @BotFather")
    print("2. Create a bot and add TELEGRAM_BOT_TOKEN to your .env file.")
    print("-----------------------------------------------------------------")
    sys.exit(1)

if not USER_ID:
    print(f"[+] Bot Token Loaded: {BOT_TOKEN[:10]}... (Connected)")
    print("[+] Status: AUTO-PAIRING MODE ACTIVE")
    print("-----------------------------------------------------------------")
    print("👉 Open Telegram on your phone right now:")
    print("   1. Open: https://t.me/Stacky016_bot")
    print("   2. Tap 'Start' (or send any message like 'Hello')")
    print("[*] Stacky will automatically pair with your phone and lock securely!")
    print("-----------------------------------------------------------------")
else:
    print(f"[+] Bot Token Configured: {BOT_TOKEN[:10]}... (Secured)")
    print(f"[+] Authorized User ID : {USER_ID} (Strict Lock Engaged)")
    print("[+] Remote bridge is ARMED and listening 24/7.")
    print("-----------------------------------------------------------------")
    print("Try sending these from your phone on Telegram:")
    print("  • 'Send me the README file'")
    print("  • 'Send me a screenshot of my screen'")
    print("  • 'Lock my Mac'")
    print("=================================================================")

from backend.comms.telegram_listener import TelegramLongPoller

poller = TelegramLongPoller()
poller.run_loop()
