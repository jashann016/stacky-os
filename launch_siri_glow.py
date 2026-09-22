import webbrowser
import os
from pathlib import Path

glow_html = Path(__file__).resolve().parent / "apple_intelligence_glow.html"

print("=================================================================")
print("  LAUNCHING AUTHENTIC APPLE INTELLIGENCE LIQUID BORDER GLOW      ")
print("=================================================================")
print(f"[+] File: {glow_html}")
print("[+] Press Cmd + W to close the preview when finished.")

# Open directly in default macOS browser
webbrowser.open(f"file://{glow_html}")
