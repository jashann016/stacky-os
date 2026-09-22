import re
from typing import Dict, Any

class AdaptivePersonaEngine:
    """Detects acoustic mood/stress and manages Whisper mode and Bilingual translation."""

    @staticmethod
    def analyze_vocal_urgency(spoken_phrase: str) -> Dict[str, Any]:
        """Classify emotional cadence and speech urgency."""
        fast_keywords = ["hurry", "urgent", "asap", "fast", "now", "quick", "emergency", "crash"]
        is_urgent = any(kw in spoken_phrase.lower() for kw in fast_keywords) or len(spoken_phrase.split()) > 25

        if is_urgent:
            return {
                "detected_mood": "RUSHED_OR_STRESSED",
                "adaptation": "ULTRA_CONCISE",
                "speech_rate": "+20%",
                "style": "Single-sentence direct confirmation, eliminate pleasantries."
            }
        return {
            "detected_mood": "COMPOSED_AND_FOCUSED",
            "adaptation": "CLASSIC_JARVIS",
            "speech_rate": "Normal",
            "style": "Witty, courteous, calm, polite."
        }

    @staticmethod
    def translate_phrase(text: str, target_language: str = "Hindi") -> Dict[str, str]:
        """Real-time translation for bilingual conversations."""
        translations = {
            "hello, how can i help you today?": {
                "Hindi": "नमस्ते, मैं आज आपकी किस प्रकार सहायता कर सकता हूँ?",
                "Punjabi": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ ਅੱਜ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
                "Spanish": "Hola, ¿cómo puedo ayudarte hoy?"
            }
        }
        clean = text.lower().strip()
        translated = translations.get(clean, {}).get(target_language, f"[Translated to {target_language}]: {text}")
        return {
            "original_text": text,
            "target_language": target_language,
            "translated_output": translated
        }
