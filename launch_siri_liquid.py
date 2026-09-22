import webbrowser
from pathlib import Path

target = Path(__file__).resolve().parent / "siri_liquid_screen_glow.html"

print("=================================================================")
print("  LAUNCHING EXACT APPLE INTELLIGENCE LIQUID SINE-WAVE GLOW       ")
print("=================================================================")
print(f"[+] Path: {target}")
print("[+] Press Cmd + W to close the preview when finished.")

webbrowser.open(f"file://{target}")
