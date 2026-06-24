"""Centralized configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    # How long Ollama keeps the model loaded in memory after a request (its
    # own default is 5m, which gets hit during normal Jarvis idle gaps and
    # forces a multi-second reload on the next request).
    OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    VOICE_LANGUAGE: str = os.getenv("VOICE_LANGUAGE", "ko")
    # Safety cap, not a fixed duration -- AudioRecorder stops as soon as it
    # detects silence after speech (see voice_recognition/recorder.py).
    RECORD_SECONDS: float = float(os.getenv("RECORD_SECONDS", "8"))

    # Edge TTS (see tts/speaker.py). Two voices because en-GB-RyanNeural
    # raises edge_tts.exceptions.NoAudioReceived on Korean text -- Jarvis
    # picks one of these per-utterance based on whether the text contains
    # Hangul.
    TTS_VOICE_KO: str = os.getenv("TTS_VOICE_KO", "ko-KR-InJoonNeural")
    TTS_VOICE_EN: str = os.getenv("TTS_VOICE_EN", "en-GB-RyanNeural")
    # +20% cuts ~25% off speaking time vs the old -10% with diminishing
    # returns past this point (+25%/+30% only save ~0.3s more on a 2-sentence
    # reply) -- see the rate comparison in the PR/chat log.
    TTS_RATE: str = os.getenv("TTS_RATE", "+20%")
    TTS_PITCH: str = os.getenv("TTS_PITCH", "-5Hz")

    # Real-time info (see realtime/). Open-Meteo needs no key; Tavily does --
    # get one at tavily.com and put it in .env, or web_search() degrades to
    # a Korean "not configured" reply.
    WEATHER_DEFAULT_CITY: str = os.getenv("WEATHER_DEFAULT_CITY", "서울")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")


settings = Settings()
