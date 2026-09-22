#!/usr/bin/env python3
"""
Stacky AI - Telegram Cloud Webhook Activator
Usage:
    python3 deploy_to_telegram_webhook.py https://stacky-ai-backend.onrender.com
"""

import sys
import os
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def set_webhook(render_url: str):
    if not BOT_TOKEN:
        print("[!] Error: TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)

    clean_url = render_url.rstrip("/")
    webhook_url = f"{clean_url}/api/telegram/webhook"
    api_endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"

    print(f"[*] Registering Telegram Webhook to Render:")
    print(f"    Webhook URL: {webhook_url}")

    req = urllib.request.Request(api_endpoint, headers={"User-Agent": "StackyCloudDeployer/1.0"})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            if res.get("ok"):
                print("[✓] SUCCESS! Telegram Webhook registered successfully.")
                print("[*] Description:", res.get("description", "Webhook was set"))
                print("\n[+] Stacky is now LIVE on Render 24/7.")
                print("[+] Any message to @Stacky016_bot goes directly to Render cloud with ZERO polling.")
            else:
                print("[✗] Telegram API returned:", res)
    except Exception as e:
        print("[✗] Failed to set webhook:", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 deploy_to_telegram_webhook.py <RENDER_PUBLIC_URL>")
        print("Example: python3 deploy_to_telegram_webhook.py https://stacky-ai-backend.onrender.com")
        sys.exit(1)

    set_webhook(sys.argv[1])
