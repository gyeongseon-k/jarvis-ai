"""Text-to-speech output.

Primary: Windows native TTS (System.Speech.Synthesis) via powershell.exe, reached
through WSL interop. Falls back to pyttsx3 if PowerShell/Windows TTS is unavailable.
"""

import os
import shutil
import subprocess
import tempfile


class Speaker:
    def __init__(self):
        self._powershell = shutil.which("powershell.exe")
        self._pyttsx3_engine = None

    def speak(self, text: str) -> None:
        """Speak `text` aloud. Tries Windows TTS first, falls back to pyttsx3."""
        text = text.strip()
        if not text:
            return

        if self._powershell and self._speak_windows(text):
            return

        if self._speak_pyttsx3(text):
            return

        print(f"[TTS 실패] 음성 출력을 사용할 수 없습니다. 텍스트: {text}")

    def _speak_windows(self, text: str) -> bool:
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)

            win_path = subprocess.run(
                ["wslpath", "-w", path], capture_output=True, text=True, check=True
            ).stdout.strip()

            # Text travels via a UTF-8 file, not the command string, so user/LLM
            # text can never be interpreted as PowerShell code.
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$text = Get-Content -LiteralPath '{win_path}' -Raw -Encoding UTF8; "
                "$synth.Speak($text)"
            )
            subprocess.run(
                [self._powershell, "-NoProfile", "-Command", script],
                timeout=30,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.SubprocessError, OSError) as e:
            print(f"[TTS] Windows TTS 호출 실패, pyttsx3로 대체합니다: {e}")
            return False
        finally:
            os.remove(path)

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            if self._pyttsx3_engine is None:
                import pyttsx3

                self._pyttsx3_engine = pyttsx3.init()
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
            return True
        except Exception as e:
            print(f"[TTS] pyttsx3도 실패했습니다: {e}")
            return False
