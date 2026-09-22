import webbrowser
from pathlib import Path

target = Path(__file__).resolve().parent / "siri_apple_intelligence_pro.html"

print("=================================================================")
print("  LAUNCHING PRO WEBGL APPLE INTELLIGENCE LIQUID SHADER GLOW      ")
print("=================================================================")
print(f"[+] Path: {target}")
print("[+] Press Cmd + W to close the preview when finished.")

webbrowser.open(f"file://{target}")
