"""State machine: wake word ("자비스") gates command processing.

IDLE -> (wake word heard) -> LISTENING -> (one command processed) -> IDLE
"""

import time
from enum import Enum, auto

from automation.commands import CommandRunner, match_command
from config.settings import settings
from llm.ollama_client import OllamaClient
from realtime.search import match_search, web_search
from realtime.weather import get_weather, match_weather
from tts.speaker import Speaker
from voice_recognition.listener import VoiceListener
from voice_recognition.wake_word import contains_wake_word, extract_command

WAKE_REPLY = "옛썰, 말씀하세요."


class State(Enum):
    IDLE = auto()
    LISTENING = auto()


class JarvisAssistant:
    def __init__(self, listener: VoiceListener, llm: OllamaClient, speaker: Speaker, runner: CommandRunner):
        self.listener = listener
        self.llm = llm
        self.speaker = speaker
        self.runner = runner
        self.state = State.IDLE
        self._running = False

    def stop(self) -> None:
        """Signal run_forever() to exit after its current iteration.

        Lets a future caller (e.g. a tray icon's "Quit" menu item, running on
        the main thread while run_forever() runs in a background thread) shut
        the loop down without relying on KeyboardInterrupt.
        """
        self._running = False

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            text = self.listener.listen()
            recording_time = self.listener.last_recording_time
            whisper_time = self.listener.last_whisper_time
            if not text:
                continue
            self.handle(text, recording_time, whisper_time)

    def handle(self, text: str, recording_time: float = 0.0, whisper_time: float = 0.0) -> None:
        """Process one recognized utterance according to the current state."""
        print(f"You: {text}")

        if self.state is State.IDLE:
            if not contains_wake_word(text):
                return

            command_text = extract_command(text)
            if command_text:
                # "자비스 + 명령" in one breath -- skip the "네, 말씀하세요"
                # round-trip and process the command right away.
                self._process(command_text, recording_time, whisper_time)
            else:
                self.state = State.LISTENING
                tts_time = self._reply(WAKE_REPLY)
                self._log_timing(recording_time, whisper_time, 0.0, tts_time)
            return

        self._process(text, recording_time, whisper_time)

    def _process(self, text: str, recording_time: float, whisper_time: float) -> None:
        """Run a command (or ask the LLM) for one already-woken utterance and reply.

        Checked in order of specificity so generic catch-alls don't steal
        utterances meant for a more specific handler -- e.g. "시간 알려줘"
        must resolve to tell_time (via match_command), not the generic
        "~ 알려줘" web-search trigger.
        """
        ollama_time = 0.0

        city = match_weather(text)
        if city is not None:
            reply = get_weather(city or settings.WEATHER_DEFAULT_CITY)
        else:
            command = match_command(text)
            if command:
                reply = self.runner.run(command)
            else:
                query = match_search(text)
                if query is not None:
                    # Includes the Tavily request + the Korean-summary LLM
                    # call (see realtime/search.py), so this no longer
                    # reads 0.0s for search queries the way it does for
                    # plain action commands.
                    t0 = time.perf_counter()
                    reply = web_search(query, self.llm)
                    ollama_time = time.perf_counter() - t0
                else:
                    t0 = time.perf_counter()
                    reply = self.llm.ask(text)
                    ollama_time = time.perf_counter() - t0

        tts_time = self._reply(reply)
        self._log_timing(recording_time, whisper_time, ollama_time, tts_time)
        self.state = State.IDLE

    def _reply(self, text: str) -> float:
        print(f"Jarvis: {text}")
        t0 = time.perf_counter()
        self.speaker.speak(text)
        return time.perf_counter() - t0

    def _log_timing(
        self, recording_time: float, whisper_time: float, ollama_time: float, tts_time: float
    ) -> None:
        total_time = recording_time + whisper_time + ollama_time + tts_time
        print("[Timing]")
        print(f"Recording: {recording_time:.1f}s")
        print(f"Whisper: {whisper_time:.1f}s")
        print(f"Ollama: {ollama_time:.1f}s")
        print(f"TTS: {tts_time:.1f}s")
        print(f"Total: {total_time:.1f}s")
