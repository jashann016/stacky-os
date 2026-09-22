import webbrowser
from pathlib import Path

target = Path(__file__).resolve().parent / "live_liquid_orb_hud.html"

print("=================================================================")
print("  LAUNCHING 4K LIVING VOICE ORB WITH AUDIO RIPPLES               ")
print("=================================================================")
print(f"[+] Path: {target}")
print("[+] Press Cmd + W to close when done.")

webbrowser.open(f"file://{target}")
