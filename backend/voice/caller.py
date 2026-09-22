import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("VoiceCaller")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER", "")

class PhoneCallDispatcher:
    """Dispatches outbound phone calls to the user's mobile phone with voice briefings."""

    def __init__(self):
        self.has_twilio = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER and USER_PHONE_NUMBER)

    def generate_briefing_speech(self, auto_replied: List[Dict[str, Any]], held_for_review: List[Dict[str, Any]]) -> str:
        """Construct crisp, authentic Jarvis briefing text."""
        speech = "Good evening, Sir. This is Stacky reporting in with your situational briefing. "
        
        if auto_replied:
            speech += f"I have autonomously handled {len(auto_replied)} routine inquiries on your behalf: "
            for item in auto_replied:
                speech += f"{item.get('summary', '')}. "
        else:
            speech += "There were no routine items requiring auto-reply. "

        if held_for_review:
            speech += f"However, I have flagged {len(held_for_review)} high-priority items that require your direct authorization: "
            for item in held_for_review:
                speech += f"{item.get('summary', '')}. "
            speech += "I have prepared initial draft responses and placed them in your holographic HUD console awaiting your green light."
        else:
            speech += "All inboxes are clear and no critical actions are pending. Have a productive evening, Sir."

        return speech

    async def trigger_outbound_call(self, speech_text: str, phone_number: str = None) -> Dict[str, Any]:
        """Trigger an outbound phone call via Twilio or simulate call audio in HUD."""
        target_number = phone_number or USER_PHONE_NUMBER
        
        if not self.has_twilio or not target_number:
            logger.info(f"[SIMULATED OUTBOUND PHONE CALL to {target_number or 'Primary Mobile'}]")
            logger.info(f"[SPEECH DIALED]: \"{speech_text}\"")
            return {
                "status": "SIMULATED_SUCCESS",
                "message": f"Simulated call dispatched to {target_number or 'User Mobile'}.",
                "speech_script": speech_text,
                "provider": "Virtual Telephony"
            }

        try:
            # Twilio integration
            webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "")
            if webhook_url:
                call = client.calls.create(
                    url=f"{webhook_url.rstrip('/')}/api/twilio/voice",
                    to=target_number,
                    from_=TWILIO_PHONE_NUMBER
                )
            else:
                # Direct TwiML with speech gather fallback
                twiml = f"""
                <Response>
                    <Say voice="Polly.Brian" language="en-GB">{speech_text}</Say>
                    <Gather input="speech" timeout="5">
                        <Say voice="Polly.Brian" language="en-GB">Do you approve, Sir?</Say>
                    </Gather>
                </Response>
                """
                call = client.calls.create(
                    twiml=twiml,
                    to=target_number,
                    from_=TWILIO_PHONE_NUMBER
                )
            return {
                "status": "CALL_DISPATCHED",
                "sid": call.sid,
                "message": f"Interactive call initiated to {target_number}.",
                "speech_script": speech_text
            }
        except Exception as e:
            logger.error(f"Failed to dispatch Twilio call: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "speech_script": speech_text
            }
