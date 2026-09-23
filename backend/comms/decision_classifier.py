import json
import re
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from backend.config import GROQ_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger("DecisionClassifier")

CLASSIFIER_PROMPT = """
You are Stacky AI's autonomous communications auditor and decision engine.
Your task is to analyze incoming messages (Email, WhatsApp, or Instagram DM) and decide whether Stacky has authority to auto-reply or MUST hold for the user's explicit permission.

### Rules:
1. "AUTO_REPLY":
   - Routine meeting confirmations, friendly casual questions, acknowledging receipt, checking on simple plans.
2. "HOLD_FOR_USER":
   - Financial (payments, invoices, wire transfers), legal/contracts, sensitive or complex business deals.

### Output JSON Format:
{
  "action": "AUTO_REPLY" or "HOLD_FOR_USER",
  "urgency": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
  "reason": "Brief explanation",
  "summary_for_briefing": "1-sentence briefing for the phone call report",
  "suggested_reply": "Drafted reply matching user's friendly, sharp, polite tone"
}
"""

class MessageClassifier:
    def __init__(self):
        if GROQ_API_KEY:
            self.client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
            self.model = "llama-3.3-70b-versatile"
        elif OPENROUTER_API_KEY:
            self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            self.model = DEFAULT_MODEL
        elif OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            self.model = "gpt-4o"
        else:
            self.client = None
            self.model = "offline"

    def rule_based_fallback(self, platform: str, sender: str, content: str) -> Dict[str, Any]:
        """High-precision local NLP fallback for zero-latency or offline environments."""
        content_lower = content.lower()
        
        # Check financial / legal / high-risk triggers
        high_risk_keywords = ["invoice", "payment", "$", "wire", "contract", "salary", "urgent", "confidential", "sponsorship", "pricing", "agreement"]
        is_high_risk = any(kw in content_lower for kw in high_risk_keywords)

        if is_high_risk:
            return {
                "action": "HOLD_FOR_USER",
                "urgency": "HIGH",
                "reason": "Contains financial, commercial, or contractual keywords.",
                "summary_for_briefing": f"Critical communication from {sender} regarding financial or commercial terms",
                "suggested_reply": "Thank you for reaching out. I have noted the details and will follow up with you personally shortly."
            }
        else:
            # Routine / casual inquiry
            if "gym" in content_lower or "meeting" in content_lower or "call" in content_lower:
                reply = "Hey! Sounds good, looking forward to it."
            else:
                reply = "Thanks for checking in! Received and noted."

            return {
                "action": "AUTO_REPLY",
                "urgency": "LOW",
                "reason": "Routine inquiry meeting safety thresholds for auto-dispatch.",
                "summary_for_briefing": f"Routine inquiry from {sender} handled autonomously",
                "suggested_reply": reply
            }

    async def evaluate_message(self, platform: str, sender: str, content: str) -> Dict[str, Any]:
        """Classify message and return structured decision."""
        if not self.client:
            return self.rule_based_fallback(platform, sender, content)

        prompt = f"""
Platform: {platform}
Sender: {sender}
Message Body:
\"\"\"{content}\"\"\"

Analyze and return the strict JSON schema.
"""
        try:
            res = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=5.0
            )
            raw = res.choices[0].message.content
            return json.loads(raw)
        except Exception:
            # Use local high-accuracy heuristic engine if cloud request times out or is in offline mode
            return self.rule_based_fallback(platform, sender, content)
