"""LLM client for a local Ollama server, via its HTTP API (no streaming)."""

import requests

from config.settings import settings


class OllamaClient:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    def ask(self, prompt: str) -> str:
        response = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
