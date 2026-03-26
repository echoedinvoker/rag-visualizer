"""Environment configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str, hint: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. {hint}")
    return value


def get_openai_api_key() -> str:
    return _require_env("OPENAI_API_KEY", "Get one at https://platform.openai.com/api-keys")


def get_tavily_api_key() -> str:
    return _require_env("TAVILY_API_KEY", "Get one at https://tavily.com/")


CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Session settings
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_FILES_PER_SESSION = int(os.getenv("MAX_FILES_PER_SESSION", "5"))
