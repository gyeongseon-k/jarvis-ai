"""State machine: wake word ("자비스") gates command processing.

IDLE -> (wake word heard) -> LISTENING -> (one command processed) -> IDLE
"""

from enum import Enum, auto

from automation.commands import CommandRunner, match_command
from llm.ollama_client import OllamaClient
from tts.speaker import Speaker
from voice_recognition.listener import VoiceListener
from voice_recognition.wake_word import contains_wake_word

WAKE_REPLY = "네, 말씀하세요."


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

    def run_forever(self) -> None:
        while True:
            text = self.listener.listen()
            if not text:
                continue
            self.handle(text)

    def handle(self, text: str) -> None:
        """Process one recognized utterance according to the current state."""
        print(f"You: {text}")

        if self.state is State.IDLE:
            if contains_wake_word(text):
                self.state = State.LISTENING
                self._reply(WAKE_REPLY)
            return

        command = match_command(text)
        reply = self.runner.run(command) if command else self.llm.ask(text)
        self._reply(reply)
        self.state = State.IDLE

    def _reply(self, text: str) -> None:
        print(f"Jarvis: {text}")
        self.speaker.speak(text)
