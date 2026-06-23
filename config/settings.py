"""Centralized configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    VOICE_LANGUAGE: str = os.getenv("VOICE_LANGUAGE", "ko")
    RECORD_SECONDS: float = float(os.getenv("RECORD_SECONDS", "5"))


settings = Settings()
