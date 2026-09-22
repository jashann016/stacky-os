import asyncio
import time
import json
from datetime import datetime
from backend.agent.core import StackyAgent
from backend.tools.os_control import get_system_diagnostics

SCENARIOS = [
    ("Communications Triage", "Scan all my inboxes and report actions taken."),
    ("Episodic Memory Recall", "Recall what my accountant told me about tax deductions."),
    ("Ghost Research Mission", "Conduct deep research on quantum computing breakthroughs."),
    ("System Telemetry Check", "What is my current battery percentage and CPU load?"),
    ("Environment Focus Mode", "Engage focus mode immediately."),
    ("Developer Ops Port Check", "Check if port 3000 is occupied and free it."),
    ("Milestone Alerting", "Check upcoming birthdays and milestones."),
    ("Biometric Voice Verification", "Verify my vocal acoustic signature authorization."),
    ("Desktop Butler Organizing", "Clean and organize my downloads directory."),
    ("Outbound Telephony Briefing", "Trigger an outbound voice briefing to my phone.")
]

async def run_soak_test(duration_seconds=600):
    agent = StackyAgent()
    start_time = time.time()
    results = []
    cycle = 0

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting 10-minute autonomous soak test for Stacky AI...")

    while (time.time() - start_time) < duration_seconds:
        cycle += 1
        scenario_idx = (cycle - 1) % len(SCENARIOS)
        test_name, prompt = SCENARIOS[scenario_idx]
        
        t0 = time.time()
        try:
            res = await agent.chat(prompt)
            latency = round(time.time() - t0, 3)
            diag = get_system_diagnostics()
            
            entry = {
                "cycle": cycle,
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "scenario": test_name,
                "prompt": prompt,
                "latency_seconds": latency,
                "tools_used": [t["name"] for t in res.get("tools_used", [])],
                "reply_snippet": res.get("reply", "")[:100],
                "cpu_load": diag.get("cpu_usage_percent", 0),
                "battery": diag.get("battery", {}).get("percentage", "N/A"),
                "status": "PASS"
            }
            results.append(entry)
            print(f"[{entry['timestamp']}] Cycle {cycle} ({test_name}) -> PASS in {latency}s | Tools: {entry['tools_used']}")
        except Exception as e:
            results.append({
                "cycle": cycle,
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "scenario": test_name,
                "status": "FAIL",
                "error": str(e)
            })
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle {cycle} ({test_name}) -> FAIL: {e}")

        # Sleep between checks
        await asyncio.sleep(45)

    # Save summary report
    with open("test_soak_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 10-Minute soak test concluded. Total cycles: {cycle}. Report saved.")

if __name__ == "__main__":
    asyncio.run(run_soak_test(600))
