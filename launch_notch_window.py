#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BINARY = BASE_DIR / "bin" / "stacky_notch_bar"
SRC_M = BASE_DIR / "macos" / "notch_overlay.m"

def ensure_compiled():
    needs_compile = False
    if not BINARY.exists():
        needs_compile = True
    elif SRC_M.exists() and SRC_M.stat().st_mtime > BINARY.stat().st_mtime:
        needs_compile = True

    if needs_compile:
        print("[+] Compiling native macOS Notch Bar binary...")
        cmd = [
            "clang", "-O2", "-fobjc-arc",
            str(SRC_M),
            "-framework", "Cocoa",
            "-framework", "WebKit",
            "-o", str(BINARY)
        ]
        res = subprocess.run(cmd, cwd=str(BASE_DIR))
        if res.returncode != 0:
            print("[-] Compilation failed.")
            sys.exit(1)
        print("[+] Compilation complete: bin/stacky_notch_bar ready.")

def main():
    ensure_compiled()
    print("=================================================================")
    print("           STACKY AI // SOVEREIGN MACOS NOTCH OVERLAY            ")
    print("=================================================================")
    print(f"[+] Native Engine Binary: {BINARY}")
    print("[+] Hardware Anchor     : Built-in MacBook Display Notch")
    print("-----------------------------------------------------------------")
    print(" 🚀 ACTIVATION SHORTCUT : Double-tap [Control]  (Ctrl + Ctrl)")
    print(" 💤 DISMISS SHORTCUT    : Press [Esc]  or  single-tap [Control]")
    print(" ⚡ ZERO BACKGROUND DRAW: 0.0% CPU & 0 mic usage when dismissed")
    print("-----------------------------------------------------------------")
    print("[+] Terminal commands: 'wake', 'sleep', 'toggle', or 'exit'")
    print("=================================================================")

    binary_args = [str(BINARY)]
    if "--show" in sys.argv:
        binary_args.append("--show")

    proc = subprocess.Popen(
        binary_args,
        cwd=str(BASE_DIR),
        stdin=subprocess.PIPE,
        text=True
    )

    try:
        while proc.poll() is None:
            user_cmd = input().strip()
            if not user_cmd:
                continue
            if user_cmd.lower() in ["exit", "quit"]:
                proc.stdin.write("exit\n")
                proc.stdin.flush()
                break
            else:
                proc.stdin.write(f"{user_cmd}\n")
                proc.stdin.flush()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        if proc.poll() is None:
            try:
                proc.stdin.write("exit\n")
                proc.stdin.flush()
                proc.terminate()
            except Exception:
                pass
        print("\n[+] Native Notch Overlay terminated gracefully.")

if __name__ == "__main__":
    main()
