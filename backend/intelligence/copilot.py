from typing import Dict, Any, List

class MeetingCopilot:
    """Passive audio ear, teleprompter, and meeting minutes compiler."""
    
    def __init__(self):
        self.meeting_active = False
        self.transcript_buffer: List[str] = []

    def start_meeting(self, meeting_title: str = "Client & Strategy Sync") -> Dict[str, str]:
        self.meeting_active = True
        self.transcript_buffer = [
            f"Meeting initialized: {meeting_title}",
            "Participant 1: 'Can we integrate the database with our current SSO architecture?'",
            "Participant 2: 'What is our expected SLA for API latency under 50k requests?'"
        ]
        return {
            "status": "RECORDING_PASSIVE",
            "title": meeting_title,
            "message": "Meeting Co-Pilot active. Listening silently and generating live teleprompter answers."
        }

    def get_live_cheat_sheet(self) -> List[Dict[str, str]]:
        """Instant cheat-sheet popups for tough technical / strategy questions."""
        return [
            {
                "detected_question": "Can we integrate the database with our current SSO architecture?",
                "suggested_answer": "Yes, Sir. Our architecture supports SAML 2.0 and OIDC with role-based access control out of the box."
            },
            {
                "detected_question": "What is our expected SLA for API latency under 50k requests?",
                "suggested_answer": "Benchmark shows p99 latency stays strictly below 180ms through edge caching and Redis connection pooling."
            }
        ]

    def stop_meeting_and_generate_minutes(self) -> Dict[str, Any]:
        self.meeting_active = False
        return {
            "title": "Strategy & Technical Architecture Sync",
            "executive_summary": "Reviewed SSO integration feasibility and latency SLAs under high throughput.",
            "action_items": [
                "Jashan: Confirm final SSO SAML provider spec by Friday.",
                "Engineering: Run load test report up to 75k concurrent queries."
            ],
            "draft_followup_email": "Hi Team, thanks for the productive sync today. As discussed, we are proceeding with SAML 2.0/OIDC integration and our p99 SLA is validated under 180ms. Detailed minutes attached. Best regards, Jashan"
        }
