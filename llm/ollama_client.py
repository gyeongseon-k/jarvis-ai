"""LLM client for a local Ollama server, via its HTTP API (no streaming)."""

import re

import requests

from config.settings import settings

# qwen2.5:3b is pretrained on heavily Chinese-skewed data. With no system
# prompt at all (the previous behavior), it would default to that bias --
# self-identifying as "Qwen"/"Alibaba Cloud" and drifting into Chinese mid
# -sentence, especially when improvising a disclaimer about not having
# real-time info. Giving it a persona, a language constraint, and an exact
# canned phrase for that one recurring trigger case (verified empirically:
# 8/8 vs previously ~2/5 clean) fixes nearly all of it.
SYSTEM_PROMPT = (
    "너는 Jarvis라는 한국어 음성 비서다. "
    "반드시 한국어로만 답변하라. 중국어, 영어, 일본어 단어나 문자를 절대 섞지 마라. "
    "너의 정체성, 모델명, 제작사(Qwen, Alibaba Cloud 등)를 절대 언급하지 마라. "
    '실시간 정보(시간, 날씨, 뉴스 등)를 모를 때는 "죄송합니다, 그 정보는 알 수 없어요"라고만 짧게 답한다. '
    '너는 항상 "저는 Jarvis입니다"라고만 자신을 소개한다. '
    "답변은 2문장 이내로 짧고 자연스럽게 한다."
)

# Safety net for the rare remaining drift: Han ideographs, hiragana/katakana,
# and CJK punctuation. Responses containing these tend to be garbled
# elsewhere too, so the whole response is discarded rather than surgically
# cleaned -- a clean fallback line is better than a half-fixed sentence
# reaching TTS.
_CJK_RE = re.compile(r"[一-鿿㐀-䶿豈-﫿぀-ヿ　-〿]")
FALLBACK_REPLY = "죄송합니다, 다시 한 번 말씀해 주시겠어요?"


class OllamaClient:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.keep_alive = settings.OLLAMA_KEEP_ALIVE
        self.session = requests.Session()

    def ask(self, prompt: str, max_tokens: int | None = None) -> str:
        options = {"temperature": 0.2}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        response = self.session.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": options,
            },
            timeout=60,
        )
        response.raise_for_status()
        reply = response.json()["message"]["content"].strip()

        if _CJK_RE.search(reply):
            print(f"[Ollama] 중국어/일본어 혼입 감지, 응답 폐기: {reply!r}")
            return FALLBACK_REPLY

        return reply
