"""
Stacky AI - Dynamic Model Router (Mixture of Specialists Cascade)
Intelligently routes every user prompt to the optimal Groq model based on:
- Latency requirements (Speed vs Deep Thought)
- Complexity & Reasoning Depth
- Language & Script (Multilingual Hindi/Punjabi vs English)
- Quota Conservation (14,400 RPD vs 1,000 RPD)
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger("DynamicRouter")

# Model definitions available on Groq
MODEL_SPEED_20B = "openai/gpt-oss-20b"          # ~0.3s latency, 14,400 RPD
MODEL_REASONING_120B = "openai/gpt-oss-120b"    # 120B frontier reasoning, 1,000 RPD
MODEL_MULTILINGUAL = "qwen/qwen3.8-27b"        # 27B Polyglot (Hindi, Punjabi, Regional)
MODEL_FALLBACK = "openai/gpt-oss-20b"

# Indic scripts Unicode ranges (Devanagari for Hindi, Gurmukhi for Punjabi)
RE_INDIC_SCRIPTS = re.compile(r"[\u0900-\u097F\u0A00-\u0A7F]")

# Common Hindi / Punjabi conversational keywords (romanized)
HINDI_PUNJABI_KEYWORDS = {
    "kida", "kiddan", "haal", "kaise", "kya", "sat", "sri", "akaal", "namaste",
    "dhanyavaad", "shukriya", "tussi", "paaji", "bhai", "yaar", "batao", "sun",
    "dasso", "punjabi", "hindi", "karda", "karde", "samjhao"
}

# Quick / Lightweight intent words (Speed Tier)
SPEED_INTENTS = {
    "hi", "hello", "hey", "who are you", "status", "ping", "test",
    "lock", "volume", "battery", "cpu", "ram", "mute", "unmute",
    "screenshot", "time", "date", "weather", "thanks", "thank you",
    "ok", "cool", "got it", "good morning", "good evening", "goodnight",
    "clear", "sleep"
}

# Deep reasoning / complex intent words (120B Reasoning Tier)
COMPLEX_INTENTS = [
    "explain", "analyze", "debug", "architect", "refactor", "algorithm",
    "compare", "write a code", "write a script", "write an essay", "summarize",
    "generate a report", "research", "draft an email", "solve", "math",
    "philosophy", "strategy", "why", "how does", "deep dive", "plan"
]

def select_optimal_model(user_input: str) -> Tuple[str, str]:
    """
    Analyzes prompt and selects the best LLM brain.
    Returns: (model_id, reason)
    """
    raw = user_input.strip()
    inp = raw.lower()
    words = set(re.findall(r"\b\w+\b", inp))

    # 1. Multilingual Tier: Devanagari / Gurmukhi script or Indic words
    if RE_INDIC_SCRIPTS.search(raw) or (words & HINDI_PUNJABI_KEYWORDS):
        logger.info(f"[Dynamic Router] Routing to Multilingual Specialist: {MODEL_MULTILINGUAL}")
        return MODEL_MULTILINGUAL, "multilingual_specialist"

    # 2. Deep Reasoning Tier: Code, Architecture, In-depth analysis
    if any(k in inp for k in COMPLEX_INTENTS) or len(raw) > 120:
        logger.info(f"[Dynamic Router] Routing to Frontier Reasoning Brain: {MODEL_REASONING_120B}")
        return MODEL_REASONING_120B, "deep_reasoning"

    # 3. Speed & Utility Tier: Short status, greetings, OS commands (< 50 chars)
    if (words & SPEED_INTENTS) or len(raw) < 50:
        logger.info(f"[Dynamic Router] Routing to Ultra-Fast Brain: {MODEL_SPEED_20B}")
        return MODEL_SPEED_20B, "instant_speed"

    # Default to 120B for high quality if ambiguous
    return MODEL_REASONING_120B, "standard_intelligence"

def get_fallback_model(failed_model: str) -> str:
    """Provides instant cascade failover if a model encounters a rate-limit."""
    if failed_model == MODEL_REASONING_120B:
        return MODEL_SPEED_20B
    elif failed_model == MODEL_MULTILINGUAL:
        return MODEL_SPEED_20B
    return MODEL_FALLBACK
