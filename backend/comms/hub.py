import asyncio
import logging
from typing import List, Dict, Any

from backend.comms.email_engine import EmailEngine
from backend.comms.social_engine import SocialInboxEngine
from backend.comms.decision_classifier import MessageClassifier
from backend.voice.caller import PhoneCallDispatcher

logger = logging.getLogger("CommsHub")

class CommunicationsHub:
    """Orchestrates ingestion across all platforms, evaluates safety, and dispatches actions."""
    
    def __init__(self):
        self.email_engine = EmailEngine()
        self.social_engine = SocialInboxEngine()
        self.classifier = MessageClassifier()
        self.caller = PhoneCallDispatcher()
        
        # State tracking
        self.auto_replied_history: List[Dict[str, Any]] = []
        self.held_for_review: List[Dict[str, Any]] = []

    async def scan_and_process_all_inboxes(self) -> Dict[str, Any]:
        """Scan Email, WhatsApp, and Instagram, classify each, and take action."""
        # 1. Fetch raw messages
        emails = self.email_engine.fetch_unread_emails(limit=3)
        socials = self.social_engine.fetch_incoming_social_messages()

        all_incoming = []
        for em in emails:
            all_incoming.append({
                "id": em["id"],
                "platform": "Email",
                "sender": em["sender"],
                "subject": em.get("subject", ""),
                "content": em.get("body", "")
            })
            
        for soc in socials:
            all_incoming.append({
                "id": soc["id"],
                "platform": soc["platform"],
                "sender": soc["sender"],
                "content": soc["content"]
            })

        new_auto_replied = []
        new_held = []

        # 2. Run decision engine on each message
        for msg in all_incoming:
            eval_result = await self.classifier.evaluate_message(
                platform=msg["platform"],
                sender=msg["sender"],
                content=msg.get("content", msg.get("subject", ""))
            )
            
            summary_entry = {
                "id": msg["id"],
                "platform": msg["platform"],
                "sender": msg["sender"],
                "content": msg["content"][:100],
                "action": eval_result.get("action", "HOLD_FOR_USER"),
                "urgency": eval_result.get("urgency", "MEDIUM"),
                "reason": eval_result.get("reason", ""),
                "summary": eval_result.get("summary_for_briefing", ""),
                "suggested_reply": eval_result.get("suggested_reply", "")
            }

            if eval_result.get("action") == "AUTO_REPLY":
                # Autonomous auto-reply
                if msg["platform"] == "Email":
                    self.email_engine.send_reply(msg["sender"], msg.get("subject", "Re: inquiry"), eval_result["suggested_reply"])
                else:
                    self.social_engine.send_social_reply(msg["platform"], msg["sender"], eval_result["suggested_reply"])
                
                new_auto_replied.append(summary_entry)
            else:
                # Hold for Tony Stark's review
                new_held.append(summary_entry)

        self.auto_replied_history.extend(new_auto_replied)
        self.held_for_review = new_held  # Update pending reviews

        return {
            "auto_replied": new_auto_replied,
            "held_for_review": new_held,
            "total_processed": len(all_incoming)
        }

    async def execute_phone_briefing(self, phone_number: str = None) -> Dict[str, Any]:
        """Generate executive Jarvis briefing and dial the user's phone."""
        speech = self.caller.generate_briefing_speech(
            auto_replied=self.auto_replied_history[-3:],
            held_for_review=self.held_for_review
        )
        call_res = await self.caller.trigger_outbound_call(speech, phone_number)
        return call_res
