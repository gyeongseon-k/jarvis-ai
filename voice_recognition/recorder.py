"""Microphone capture via `parec`, using WSLg's PulseAudio bridge."""

import shutil
import subprocess
import time


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        if shutil.which("parec") is None:
            raise RuntimeError(
                "'parec' not found. Install it with: sudo apt install pulseaudio-utils"
            )
        self.sample_rate = sample_rate
        self.channels = channels

    def record(self, duration: float, output_path: str) -> str:
        """Record `duration` seconds from the default mic into a WAV file at output_path."""
        cmd = [
            "parec",
            f"--rate={self.sample_rate}",
            f"--channels={self.channels}",
            "--format=s16le",
            "--file-format=wav",
            output_path,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        time.sleep(duration)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return output_path
