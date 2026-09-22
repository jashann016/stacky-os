import os
import re
import time
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from backend.comms.telegram_bridge import telegram_bridge
from backend.agent.core import StackyAgent

logger = logging.getLogger("TelegramListener")
logging.basicConfig(level=logging.INFO)

class TelegramLongPoller:
    """Listens for remote commands sent from your phone via Telegram and executes them on your home Mac."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.allowed_user_id = str(os.getenv("TELEGRAM_ALLOWED_USER_ID", "")).strip()
        self.agent = StackyAgent()
        self.last_update_id = 0
        self.running = True

    def poll_once(self):
        if not self.bot_token:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={self.last_update_id + 1}&timeout=20"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not data.get("ok"):
                    return

                for update in data.get("result", []):
                    self.last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    sender_id = str(msg.get("from", {}).get("id", ""))
                    text = msg.get("text", "").strip()

                    # Auto-Pairing Logic: If no user ID is locked yet, pair with the first user who starts the bot
                    if not self.allowed_user_id:
                        self.allowed_user_id = sender_id
                        telegram_bridge.allowed_user_id = sender_id
                        os.environ["TELEGRAM_ALLOWED_USER_ID"] = sender_id
                        
                        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
                        if env_path.exists():
                            c = env_path.read_text(encoding="utf-8")
                            c = re.sub(r"TELEGRAM_ALLOWED_USER_ID=.*", f"TELEGRAM_ALLOWED_USER_ID={sender_id}", c)
                            env_path.write_text(c, encoding="utf-8")

                        logger.info(f"[+] Pair Successful! Locked to User ID: {sender_id}")
                        welcome_msg = (
                            "⚡ *STACKY AI // PAIRING COMPLETE*\n\n"
                            "Welcome, Sir. Your Mac at home is now securely linked to this chat.\n"
                            "🔒 *Strict Security Lock Engaged:* Only this phone can command your Mac.\n\n"
                            "Try sending:\n"
                            "• *Send me the README file*\n"
                            "• *Send me a screenshot*\n"
                            "• *What is my battery level?*\n"
                            "• *Lock my Mac*"
                        )
                        telegram_bridge.send_text_message(welcome_msg)
                        continue

                    # Security Verification: Only execute if sent by authorized user ID
                    if self.allowed_user_id and sender_id != self.allowed_user_id:
                        logger.warning(f"Unauthorized access attempt rejected from ID: {sender_id}")
                        continue

                    if not text:
                        continue

                    logger.info(f"[Remote Phone Command Received]: '{text}'")

                    # 1. Check if it's a file, screenshot, or hardware command
                    if any(k in text.lower() for k in ["send me", "fetch", "screenshot", "lock"]):
                        reply = telegram_bridge.handle_remote_command(text)
                        telegram_bridge.send_text_message(reply)
                    else:
                        # 2. General conversation / question with Stacky Brain
                        import asyncio
                        agent_res = asyncio.run(self.agent.chat(text))
                        reply_text = agent_res.get("reply", "Task completed, Sir.")
                        telegram_bridge.send_text_message(reply_text)

        except Exception as e:
            logger.debug(f"Poll timeout or connection error: {e}")

    def run_loop(self):
        logger.info("[Telegram Remote Listener]: Armed. Standing by for remote commands from your phone.")
        while self.running:
            try:
                self.poll_once()
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(2)

if __name__ == "__main__":
    poller = TelegramLongPoller()
    poller.run_loop()
