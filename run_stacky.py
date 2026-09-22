#!/usr/bin/env python3
import uvicorn
import webbrowser
import time
import threading

def open_browser():
    time.sleep(1.2)
    print("\n[+] Launching Stacky AI Holographic HUD interface at http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=======================================================")
    print("      INITIALIZING STACKY AI // PROTOCOL JARVIS        ")
    print("=======================================================")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
