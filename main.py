"""Entry point for the Jarvis AI voice assistant.

Step 1: mic capture (parec) -> STT (faster-whisper).
Step 2: TTS (Windows native voice via PowerShell, pyttsx3 fallback).
Step 3: LLM (Ollama qwen2.5:3b) generates replies.
Step 4: action commands (e.g. "크롬 열어") run locally instead of going to the LLM.
Step 5: wake word ("자비스") gates command processing via JarvisAssistant's state machine.
"""

from assistant import JarvisAssistant
from automation.commands import CommandRunner
from config.settings import settings
from llm.ollama_client import OllamaClient
from tts.speaker import Speaker
from voice_recognition.listener import VoiceListener


def main():
    listener = VoiceListener(language=settings.VOICE_LANGUAGE, record_seconds=settings.RECORD_SECONDS)
    llm = OllamaClient()
    speaker = Speaker()
    runner = CommandRunner()
    assistant = JarvisAssistant(listener, llm, speaker, runner)

    speaker.speak("자비스 음성 출력 테스트입니다.")
    print("Jarvis is idle. Say '자비스' to wake it. (Ctrl+C to exit)")

    try:
        assistant.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down Jarvis.")


if __name__ == "__main__":
    main()
