"""Text-to-speech output.

Primary: Microsoft Edge TTS (edge-tts) for synthesis, pygame.mixer for
playback. Both run entirely on the WSL/Linux side -- WSLg bridges audio to
the Windows host via PulseAudio, so no Windows-side PowerShell/MediaPlayer
hop is needed. (That hop was the actual bug: MediaPlayer reported a clean
exit code with no error, but produced no audio -- confirmed by the same MP3
playing correctly when opened directly in Windows Explorer.)

Falls back to pyttsx3 if Edge TTS or pygame playback fails.
"""

import asyncio
import os
import re
import tempfile
import time
import traceback

from config.settings import settings

_HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")


def _select_voice(text: str) -> str:
    """en-GB-RyanNeural raises edge_tts.exceptions.NoAudioReceived on Korean
    text, so pick the Korean voice whenever the text contains Hangul."""
    return settings.TTS_VOICE_KO if _HANGUL_RE.search(text) else settings.TTS_VOICE_EN


class Speaker:
    def __init__(self):
        self._mixer_ready = False
        self._pyttsx3_engine = None

    def speak(self, text: str) -> None:
        """Speak `text` aloud. Tries Edge TTS + pygame first, falls back to pyttsx3."""
        text = text.strip()
        if not text:
            return

        mp3_path = self._synthesize(text)
        if mp3_path:
            played = self._play(mp3_path)
            os.remove(mp3_path)
            if played:
                return

        if self._speak_pyttsx3(text):
            return

        print(f"[TTS 실패] 음성 출력을 사용할 수 없습니다. 텍스트: {text}")

    def _synthesize(self, text: str) -> str | None:
        """Synthesize `text` to a temp MP3 via Edge TTS. Returns the file path
        on success, None on failure."""
        fd, mp3_path = tempfile.mkstemp(prefix="jarvis_tts_", suffix=".mp3")
        os.close(fd)

        voice = _select_voice(text)
        print(f"[Speaker] voice={voice}")
        print(f"[Speaker] rate={settings.TTS_RATE}")
        print(f"[Speaker] pitch={settings.TTS_PITCH}")
        print(f"[Speaker] text={text}")

        try:
            asyncio.run(self._synthesize_async(text, mp3_path, voice))
            size = os.path.getsize(mp3_path)
            print(f"[Speaker] file={mp3_path} size={size} bytes")
            if size == 0:
                print("[Speaker] 경고: 생성된 mp3 파일 크기가 0바이트입니다.")
            return mp3_path
        except Exception:
            print("[Speaker] Edge TTS 합성 실패")
            traceback.print_exc()
            os.remove(mp3_path)
            return None

    async def _synthesize_async(self, text: str, out_path: str, voice: str) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text,
            voice=voice,
            rate=settings.TTS_RATE,
            pitch=settings.TTS_PITCH,
        )
        await communicate.save(out_path)

    def _play(self, mp3_path: str) -> bool:
        """Play `mp3_path` via pygame.mixer, blocking until playback finishes.
        Independent of synthesis, so it can be re-run against an
        already-generated file while debugging."""
        try:
            import pygame

            if not self._mixer_ready:
                pygame.mixer.init()
                self._mixer_ready = True

            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()
            print(f"[Speaker] 재생 시작: {mp3_path}")
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            print("[Speaker] 재생 완료")
            return True
        except Exception:
            print("[Speaker] pygame 재생 실패")
            traceback.print_exc()
            return False

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Speaker 합성/재생 단계를 분리해서 디버깅하는 도구")
    sub = parser.add_subparsers(dest="command", required=True)

    synth_p = sub.add_parser("synth", help="텍스트 -> mp3 합성만 수행 (재생 없음, 파일 보존)")
    synth_p.add_argument("text")

    play_p = sub.add_parser("play", help="이미 생성된 mp3 파일 재생만 수행 (합성 없음)")
    play_p.add_argument("path")

    speak_p = sub.add_parser("speak", help="합성 + 재생 전체 파이프라인 수행")
    speak_p.add_argument("text")

    args = parser.parse_args()
    speaker = Speaker()

    if args.command == "synth":
        path = speaker._synthesize(args.text)
        print(f"[Speaker] 결과: {path}")
    elif args.command == "play":
        ok = speaker._play(args.path)
        print(f"[Speaker] 결과: {ok}")
    elif args.command == "speak":
        speaker.speak(args.text)
