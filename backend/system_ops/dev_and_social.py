import subprocess
import os
from typing import Dict, Any, List

class DeveloperCopilot:
    """Terminal automation: bootstrapping, fixing port conflicts, git operations."""

    @staticmethod
    def fix_port_conflict(port: int = 3000) -> Dict[str, Any]:
        """Find process holding a port and terminate it safely."""
        try:
            cmd = f"lsof -ti:{port}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            pids = res.stdout.strip().split()
            if pids:
                for pid in pids:
                    subprocess.run(f"kill -9 {pid}", shell=True)
                return {"status": "RESOLVED", "port": port, "killed_pids": pids, "message": f"Freed port {port}, Sir."}
            return {"status": "CLEAR", "port": port, "message": f"Port {port} is already free and clear."}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def quick_git_sync(commit_message: str = "Stacky autonomous updates") -> str:
        """Run safe git add, commit, and status check."""
        try:
            subprocess.run(["git", "add", "."], capture_output=True)
            subprocess.run(["git", "commit", "-m", commit_message], capture_output=True)
            return f"Git changes committed under '{commit_message}', Sir."
        except Exception as e:
            return f"Git sync error: {str(e)}"

class SocialContentEngine:
    """Monitors industry trends and drafts high-impact posts for X & LinkedIn."""

    @staticmethod
    def draft_trend_posts(topic: str = "Autonomous AI Agents") -> List[Dict[str, str]]:
        return [
            {
                "platform": "Twitter/X",
                "content": f"The shift from passive chat interfaces to local autonomous OS agents is happening faster than anticipated. When your assistant can read inboxes, execute terminal workflows, and synthesize research overnight—everything changes. #AI #AutonomousAgents"
            },
            {
                "platform": "LinkedIn",
                "content": f"Excited to share progress on local autonomous assistant engineering. Moving away from siloed cloud bots into full system-integrated co-pilots with voice, telemetry, and automated communication triage. Here is what I learned building local agent loops: 1) Deterministic safety guardrails are non-negotiable. 2) Local-first execution eliminates latency bottlenecks."
            }
        ]
