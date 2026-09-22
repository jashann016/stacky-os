import subprocess
import shutil

def send_mac_notification(title: str, subtitle: str, message: str):
    """Deliver a native macOS banner notification quietly without stealing focus or opening windows."""
    try:
        # Sanitize double quotes
        clean_title = title.replace('"', '\\"')
        clean_sub = subtitle.replace('"', '\\"')
        clean_msg = message.replace('"', '\\"')
        
        script = f'display notification "{clean_msg}" with title "{clean_title}" subtitle "{clean_sub}" sound name "Tink"'
        subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
    except Exception:
        pass
