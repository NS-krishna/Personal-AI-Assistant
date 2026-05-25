"""
config.py — Central configuration for the Personal AI Agent.

Loads all environment variables from .env and exposes them
as typed attributes on a frozen Settings dataclass.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application-wide settings loaded from environment."""

    # --- Groq (Cloud LLM) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Ollama (Local LLM) ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder")

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # --- Google OAuth ---
    GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
    GOOGLE_TOKEN_PATH: str = os.getenv("GOOGLE_TOKEN_PATH", "./token.json")

    # --- FastAPI ---
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # --- Whisper ---
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")


# Singleton instance — import this everywhere
settings = Settings()
