"""Microphone capture via `parec`, using WSLg's PulseAudio bridge.

Stops as soon as the user stops talking (silence detection on RMS amplitude)
instead of always recording for a fixed duration -- `max_seconds` is just a
safety cap for unusually long utterances or a stuck-open mic.
"""

import audioop
import shutil
import subprocess
import wave


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold: int = 500,
        silence_duration: float = 0.4,
        chunk_seconds: float = 0.05,
        no_speech_timeout: float = 2.5,
    ):
        if shutil.which("parec") is None:
            raise RuntimeError(
                "'parec' not found. Install it with: sudo apt install pulseaudio-utils"
            )
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.chunk_seconds = chunk_seconds
        self.no_speech_timeout = no_speech_timeout

    def record(self, max_seconds: float, output_path: str) -> str:
        """Record from the default mic into a WAV file at output_path, stopping
        once `silence_duration` seconds of silence follow detected speech, or
        once `no_speech_timeout` elapses with no speech detected at all,
        whichever comes first (with `max_seconds` as a hard fallback cap)."""
        chunk_bytes = int(self.sample_rate * self.channels * 2 * self.chunk_seconds)
        cmd = [
            "parec",
            f"--rate={self.sample_rate}",
            f"--channels={self.channels}",
            "--format=s16le",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        frames = bytearray()
        elapsed = 0.0
        speaking = False
        silence_elapsed = 0.0

        try:
            while elapsed < max_seconds:
                chunk = proc.stdout.read(chunk_bytes)
                if not chunk:
                    break
                frames += chunk
                elapsed += self.chunk_seconds

                amplitude = audioop.rms(chunk, 2)
                if amplitude >= self.silence_threshold:
                    speaking = True
                    silence_elapsed = 0.0
                elif speaking:
                    silence_elapsed += self.chunk_seconds
                    if silence_elapsed >= self.silence_duration:
                        break
                elif elapsed >= self.no_speech_timeout:
                    # Nobody has said anything at all yet -- don't keep
                    # listening all the way out to max_seconds.
                    break
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(bytes(frames))

        return output_path
