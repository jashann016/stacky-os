import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend"

# Only load .env if it exists in the project root directory
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

# Groq / OpenRouter / OpenAI Key configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default Model: Fast reasoning model on Groq
DEFAULT_MODEL = os.getenv("STACKY_MODEL", "openai/gpt-oss-120b")

# Telegram Remote Bridge Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")

# Security & Sovereign Master Authorization Key
STACKY_MASTER_KEY = os.getenv("STACKY_MASTER_KEY", "923352")

# Assistant Persona
ASSISTANT_NAME = "Stacky"
CREATOR_NAME = "Sir"
VOICE_NAME = "en-GB-RyanNeural"  # Jarvis-style British voice
