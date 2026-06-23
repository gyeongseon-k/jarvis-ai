"""Speech-to-text: records from the mic via parec, transcribes with faster-whisper."""

import os
import tempfile

from faster_whisper import WhisperModel

from voice_recognition.recorder import AudioRecorder


class VoiceListener:
    def __init__(self, model_size: str = "small", language: str = "ko", record_seconds: float = 5.0):
        self.recorder = AudioRecorder()
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language
        self.record_seconds = record_seconds

    def listen(self) -> str:
        """Record from the mic and return the transcribed text."""
        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            self.recorder.record(self.record_seconds, wav_path)
            segments, _ = self.model.transcribe(wav_path, language=self.language)
            return "".join(segment.text for segment in segments).strip()
        finally:
            os.remove(wav_path)
