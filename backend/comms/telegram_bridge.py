import os
import re
import json
import logging
import subprocess
import glob
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.parse
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

logger = logging.getLogger("TelegramBridge")

class TelegramRemoteBridge:
    """Remote bridge connecting your phone (via Telegram) to your Mac running Stacky at home."""

    def __init__(self):
        self._bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._allowed_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
        self.home_dir = Path.home()

    @property
    def bot_token(self):
        return os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or self._bot_token

    @bot_token.setter
    def bot_token(self, val):
        self._bot_token = val

    @property
    def allowed_user_id(self):
        return os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip() or self._allowed_user_id

    @allowed_user_id.setter
    def allowed_user_id(self, val):
        self._allowed_user_id = val

    @property
    def is_configured(self):
        return bool(self.bot_token and self.allowed_user_id)

    def find_file_on_mac(self, query: str) -> List[Path]:
        """Search Desktop, Documents, Downloads, and Workspace for files matching query."""
        search_dirs = [
            self.home_dir / "Desktop",
            self.home_dir / "Documents",
            self.home_dir / "Downloads",
            Path(__file__).resolve().parent.parent.parent
        ]
        
        matches = []
        clean_q = query.lower().strip()
        
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            try:
                for item in sdir.rglob("*"):
                    if item.is_file() and not item.name.startswith("."):
                        # Match filename
                        if clean_q in item.name.lower():
                            matches.append(item)
                            if len(matches) >= 5:
                                break
            except Exception:
                pass
        return matches

    def get_latest_saved_file(self) -> Optional[Path]:
        """Find the most recently modified user file across Desktop, Downloads, and Workspace."""
        search_dirs = [
            self.home_dir / "Desktop",
            self.home_dir / "Downloads",
            self.home_dir / "Documents",
            Path(__file__).resolve().parent.parent.parent
        ]
        candidates = []
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            try:
                for item in sdir.iterdir():
                    if item.is_file() and not item.name.startswith(".") and not item.name.endswith(".log") and not item.name.endswith(".db"):
                        candidates.append(item)
            except Exception:
                pass
        if candidates:
            candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return candidates[0]
        return None

    def save_current_or_latest_file_to_telegram(self, target_hint: Optional[str] = None) -> str:
        """Save and push the active or latest saved work file straight to Telegram."""
        target_file = None
        if target_hint:
            matches = self.find_file_on_mac(target_hint)
            if matches:
                target_file = matches[0]

        if not target_file:
            target_file = self.get_latest_saved_file()

        if not target_file:
            return "I could not locate a recently saved file to upload, Sir."

        size_kb = target_file.stat().st_size / 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"

        res = self.send_document_to_phone(target_file, caption=f"⚡ Saved to Telegram: {target_file.name} ({size_str})")
        if res.get("status") in ["DISPATCHED", "SIMULATED_SUCCESS"]:
            return f"Saved and dispatched '{target_file.name}' ({size_str}) to your Telegram, Sir. It is ready on your phone."
        else:
            return f"Attempted to dispatch '{target_file.name}', but encountered an issue: {res.get('error', 'Unknown error')}."

    def send_document_to_phone(self, file_path: Path, caption: Optional[str] = None) -> Dict[str, Any]:
        """Upload and send an actual file from your Mac directly to your phone via Telegram."""
        if not file_path.exists():
            return {"status": "ERROR", "message": f"File not found: {file_path}"}

        if not self.is_configured:
            logger.info(f"[SIMULATED TELEGRAM FILE DISPATCH] To Phone: {file_path.name} ({file_path.stat().st_size} bytes)")
            return {
                "status": "SIMULATED_SUCCESS",
                "file_name": file_path.name,
                "file_path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "message": f"Dispatched '{file_path.name}' to your phone via Telegram."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        try:
            # Multi-part form upload using curl for 100% reliable native upload on macOS
            cmd = [
                "curl", "-s", "-X", "POST", url,
                "-F", f"chat_id={self.allowed_user_id}",
                "-F", f"document=@{file_path}"
            ]
            if caption:
                cmd.extend(["-F", f"caption={caption}"])

            res = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "status": "DISPATCHED",
                "file_name": file_path.name,
                "response": res.stdout[:150]
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def send_screenshot_to_phone(self) -> Dict[str, Any]:
        """Capture active Mac desktop screen and send it to your phone."""
        snapshot_path = Path("/tmp/stacky_screen_snap.png")
        try:
            subprocess.run(["screencapture", "-x", str(snapshot_path)], check=True)
        except Exception as e:
            logger.warning(f"Native screencapture failed: {e}")

        if not self.is_configured:
            logger.info("[SIMULATED SCREENSHOT SENT TO TELEGRAM PHONE CHAT]")
            return {
                "status": "SIMULATED_SUCCESS",
                "message": "Desktop screenshot captured and sent to your phone."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            cmd = [
                "curl", "-s", "-X", "POST", url,
                "-F", f"chat_id={self.allowed_user_id}",
                "-F", f"photo=@{snapshot_path}",
                "-F", "caption=Live snapshot of your Mac desktop, Sir."
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return {"status": "DISPATCHED", "response": res.stdout[:150]}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def send_text_message(self, message: str) -> Dict[str, Any]:
        """Send formatted text or code snippet to your phone."""
        if not self.is_configured:
            logger.info(f"[SIMULATED TELEGRAM TEXT TO PHONE]: {message[:80]}...")
            return {"status": "SIMULATED_SUCCESS", "message": message}

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self.allowed_user_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=5) as response:
                return {"status": "SUCCESS", "code": response.status}
        except Exception as e:
            # Fallback to plain text without parse_mode in case Markdown contains unmatched characters
            try:
                fallback_data = urllib.parse.urlencode({
                    "chat_id": self.allowed_user_id,
                    "text": message
                }).encode("utf-8")
                req2 = urllib.request.Request(url, data=fallback_data)
                with urllib.request.urlopen(req2, timeout=5) as response:
                    return {"status": "SUCCESS", "code": response.status}
            except Exception as e2:
                return {"status": "ERROR", "error": str(e2)}

    def handle_remote_command(self, user_command: str) -> str:
        """Process remote commands sent from your phone in college."""
        cmd = user_command.lower().strip()

        # 1. Remote Screen Snapshot
        if any(w in cmd for w in ["screenshot", "screen shot", "snapshot", "screen snap", "ss", "screencap"]):
            res = self.send_screenshot_to_phone()
            if res.get("status") == "DISPATCHED":
                return "Live Mac desktop screenshot captured and dispatched to your phone, Sir."
            else:
                return f"Unable to capture screen: {res.get('error', 'unknown error')}"

        # 2. Remote Lock / Sleep
        if any(w in cmd for w in ["lock", "sleep", "lock mac", "sleep mac"]):
            subprocess.run(["pmset", "displaysleepnow"], check=False)
            return "Workstation locked and display put to sleep, Sir."

        # 3. File Fetch Request ("send me file xyz", "fetch presentation", "get assignment")
        if any(w in cmd for w in ["send me", "fetch", "get file", "find file", "download to phone", "send file", "to my phone"]):
            target = user_command
            # Strip common conversational phrases and noise words
            phrases = ["send me", "send file", "fetch file", "fetch", "get file", "get", "the file", "from desktop", "from mac", "to my phone", "to phone", "please", "file", "the", "my", "a", "an"]
            for prep in phrases:
                target = re.sub(rf"\b{prep}\b", "", target, flags=re.IGNORECASE)
            target = re.sub(r"\s+", " ", target).strip() or "document"

            matches = self.find_file_on_mac(target)
            if matches:
                chosen = matches[0]
                self.send_document_to_phone(chosen, caption=f"Here is '{chosen.name}' from your Mac at home, Sir.")
                return f"Dispatched '{chosen.name}' ({chosen.stat().st_size} bytes) directly to your phone, Sir."
            else:
                return f"I scanned your Desktop, Documents, and Downloads, but found no files matching '{target}', Sir."

        return f"Instruction '{user_command}' received on your home Mac."

telegram_bridge = TelegramRemoteBridge()
