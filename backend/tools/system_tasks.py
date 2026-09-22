import subprocess
import os
from pathlib import Path
from typing import Dict, Any

SAFE_BASE_DIR = Path.home()

def execute_shell_command(command: str) -> str:
    """Execute a safe shell command for the user and return output."""
    # Guard against obviously catastrophic commands
    blocked = ["rm -rf /", "mkfs", ":(){ :|:& };:"]
    for b in blocked:
        if b in command:
            return "Command denied: Safety protocols prohibit destructive system-wide commands, Sir."
    
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.home())
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode != 0:
            return f"Process finished with code {proc.returncode}.\nStderr: {err}\nStdout: {out}"
        return out if out else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command execution timed out after 30 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"

def capture_screen_snapshot() -> str:
    """Capture current macOS screen to analyze what the user is working on."""
    try:
        tmp_path = "/tmp/stacky_screen.png"
        res = subprocess.run(["screencapture", "-x", "-C", tmp_path], capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(tmp_path):
            return tmp_path
        return "Failed to capture screen image."
    except Exception as e:
        return f"Screen capture error: {str(e)}"
