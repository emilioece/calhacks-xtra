import os
from dotenv import load_dotenv


load_dotenv()


LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

# API keys for vision models
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# CORS and server config
ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
INGEST_PORT: int = int(os.getenv("INGEST_PORT", "8000"))


