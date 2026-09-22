import webbrowser
from pathlib import Path

target = Path(__file__).resolve().parent / "orb_animation_gallery.html"

print("=================================================================")
print("  LAUNCHING STACKY VOICE ANIMATION LAB                           ")
print("=================================================================")
print(f"[+] Path: {target}")
print("[+] Review all 4 living styles side-by-side.")

webbrowser.open(f"file://{target}")
