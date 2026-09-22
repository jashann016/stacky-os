import subprocess
import psutil
import json
from typing import Dict, Any

def run_applescript(script: str) -> str:
    """Execute AppleScript for Mac OS automation."""
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
        return f"Error: {proc.stderr.strip()}"
    except Exception as e:
        return f"Execution error: {str(e)}"

def open_application(app_name: str) -> str:
    """Open an installed macOS application."""
    res = run_applescript(f'tell application "{app_name}" to activate')
    if "Error" not in res:
        return f"Application '{app_name}' activated, Sir."
    # Fallback to shell 'open -a'
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return f"Opened '{app_name}' via system launcher."
    except Exception as e:
        return f"Could not launch '{app_name}': {str(e)}"

def close_application(app_name: str) -> str:
    """Close/quit an application."""
    res = run_applescript(f'tell application "{app_name}" to quit')
    if "Error" not in res:
        return f"Closed '{app_name}'."
    return f"Could not close '{app_name}': {res}"

def set_system_volume(level: int) -> str:
    """Set volume between 0 and 100."""
    level = max(0, min(100, level))
    script = f"set volume output volume {level}"
    run_applescript(script)
    return f"Audio output volume set to {level}%."

def get_system_volume() -> str:
    """Get current output volume."""
    vol = run_applescript("output volume of (get volume settings)")
    return f"Current volume is at {vol}%."

def get_system_diagnostics() -> Dict[str, Any]:
    """Retrieve live CPU, Memory, Disk, and Battery diagnostics."""
    cpu_percent = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()
    
    battery_info = {
        "percentage": battery.percent if battery else "N/A",
        "power_plugged": battery.power_plugged if battery else True
    }
    
    return {
        "cpu_usage_percent": cpu_percent,
        "memory_used_gb": round((mem.total - mem.available) / (1024**3), 2),
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "memory_percent": mem.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "battery": battery_info
    }

def lock_screen() -> str:
    """Lock macOS screen immediately."""
    script = 'tell application "System Events" to key code 12 using {control down, command down}'
    run_applescript(script)
    return "Workstation screen locked, Sir."

def media_play_pause() -> str:
    """Toggle play/pause for Spotify or Apple Music."""
    script = '''
    tell application "System Events"
        key code 16 using {}
    end tell
    '''
    # Alternatively check running players
    spotify_check = run_applescript('if application "Spotify" is running then tell application "Spotify" to playpause')
    if "Error" not in spotify_check and spotify_check != "":
        return "Toggled Spotify media playback."
    music_check = run_applescript('if application "Music" is running then tell application "Music" to playpause')
    return "Toggled system media playback."

def media_next() -> str:
    """Skip to next media track."""
    res = run_applescript('if application "Spotify" is running then tell application "Spotify" to next track')
    return "Skipped to next track, Sir."

def media_previous() -> str:
    """Go to previous media track."""
    res = run_applescript('if application "Spotify" is running then tell application "Spotify" to previous track')
    return "Rewound to previous track, Sir."
