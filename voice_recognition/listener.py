"""Speech-to-text: records from the mic via parec, transcribes with faster-whisper."""

import os
import tempfile
import time

from faster_whisper import WhisperModel

from voice_recognition.recorder import AudioRecorder


class VoiceListener:
    def __init__(self, model_size: str = "small", language: str = "ko", record_seconds: float = 8.0):
        """`record_seconds` is a max-duration safety cap; actual recording
        stops earlier once the recorder detects silence after speech."""
        self.recorder = AudioRecorder()
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language
        self.record_seconds = record_seconds
        # Timing of the most recent listen() call, broken down by stage (see assistant.py's [Timing] log).
        self.last_recording_time = 0.0
        self.last_whisper_time = 0.0

    def listen(self) -> str:
        """Record from the mic and return the transcribed text."""
        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            t0 = time.perf_counter()
            self.recorder.record(self.record_seconds, wav_path)
            self.last_recording_time = time.perf_counter() - t0

            t0 = time.perf_counter()
            segments, _ = self.model.transcribe(wav_path, language=self.language)
            # segments is a lazy generator -- actual decoding happens during
            # this join, not during the transcribe() call above, so both
            # must be inside the timed block to measure real inference time.
            text = "".join(segment.text for segment in segments).strip()
            self.last_whisper_time = time.perf_counter() - t0

            return text
        finally:
            os.remove(wav_path)
