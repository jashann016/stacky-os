#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BINARY = BASE_DIR / "bin" / "stacky_notch_bar"
SWIFT_SRC = BASE_DIR / "macos" / "notch_overlay.m"

def ensure_compiled():
    if not BINARY.exists():
        print("[+] Compiling native macOS Notch Bar binary...")
        cmd = [
            "clang", "-O2",
            str(SWIFT_SRC),
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
    print("=======================================================")
    print("       STACKY AI // NATIVE MACOS NOTCH OVERLAY         ")
    print("=======================================================")
    print(f"[+] Launching native overlay from: {BINARY}")
    print("[+] Positioned right under MacBook Camera Notch.")
    print("[+] Type 'toggle' to hide/show, or 'exit' to quit.")
    print("-------------------------------------------------------")

    proc = subprocess.Popen(
        [str(BINARY)],
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
