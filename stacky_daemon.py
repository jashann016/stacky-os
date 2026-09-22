#!/usr/bin/env python3
import time
import json
import asyncio
import os
import sys
from pathlib import Path
from backend.agent.core import StackyAgent
from backend.comms.hub import CommunicationsHub
from backend.tools.os_control import get_system_diagnostics
from backend.system_ops.mac_notifier import send_mac_notification

PROFILE_FILE = Path(__file__).resolve().parent / "user_profile.json"
PID_FILE = Path(__file__).resolve().parent / "stacky_daemon.pid"

class StackyBackgroundDaemon:
    """The silent, always-on Jarvis background daemon with zero windows."""

    def __init__(self):
        self.agent = StackyAgent()
        self.comms = CommunicationsHub()
        self.profile = json.loads(PROFILE_FILE.read_text())
        self.running = True
        self.scan_cycle = 0

    def write_pid(self):
        PID_FILE.write_text(str(os.getpid()))

    async def periodic_watcher(self):
        """Silently monitor inboxes, appointments, and system health in the background."""
        send_mac_notification(
            title="Stacky AI",
            subtitle="Background Core Armed",
            message=f"Autonomous daemon active for {self.profile['call_sign']}. Zero windows mode."
        )
        print(f"[{time.strftime('%H:%M:%S')}] [+] Stacky Daemon armed with PID {os.getpid()}. Zero UI active.", flush=True)

        while self.running:
            self.scan_cycle += 1
            try:
                # 1. Silently scan inboxes (Email, WhatsApp, Instagram)
                scan_res = await self.comms.scan_and_process_all_inboxes()
                auto_count = len(scan_res.get("auto_replied", []))
                held_count = len(scan_res.get("held_for_review", []))

                if held_count > 0:
                    first_held = scan_res["held_for_review"][0]
                    subject = first_held.get("subject", "Priority Action Required")
                    send_mac_notification(
                        title="Stacky AI • Priority Alert",
                        subtitle=f"{held_count} item(s) awaiting your decision",
                        message=subject[:60]
                    )
                    print(f"[{time.strftime('%H:%M:%S')}] Stacky: Flagged {held_count} priority items.", flush=True)

                elif auto_count > 0:
                    send_mac_notification(
                        title="Stacky AI • Autonomous Action",
                        subtitle="Resolved Routine Correspondence",
                        message=f"{auto_count} routine inquiries processed and answered."
                    )
                    print(f"[{time.strftime('%H:%M:%S')}] Stacky: Autonomously resolved {auto_count} routine items.", flush=True)

                # 2. Heartbeat diagnostics
                diag = get_system_diagnostics()
                print(f"[{time.strftime('%H:%M:%S')}] Stacky Telemetry: CPU {diag.get('cpu_load_percent', 'OK')}% | Mem {diag.get('memory_used_percent', 'OK')}%", flush=True)

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Daemon warning: {e}", flush=True)

            # Sleep 60 seconds between scan passes
            await asyncio.sleep(60)

    def start(self):
        self.write_pid()
        try:
            asyncio.run(self.periodic_watcher())
        except (KeyboardInterrupt, SystemExit):
            print("\nDaemon stopped gracefully.", flush=True)
        finally:
            if PID_FILE.exists():
                try:
                    PID_FILE.unlink()
                except Exception:
                    pass

if __name__ == "__main__":
    daemon = StackyBackgroundDaemon()
    daemon.start()
