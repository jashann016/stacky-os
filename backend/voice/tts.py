import edge_tts
import asyncio
import io
from pathlib import Path
from backend.config import VOICE_NAME

async def synthesize_speech(text: str, voice: str = VOICE_NAME) -> bytes:
    """Synthesize high fidelity voice using neural TTS and return raw mp3 bytes."""
    communicate = edge_tts.Communicate(text, voice)
    mp3_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_buffer.write(chunk["data"])
    return mp3_buffer.getvalue()
