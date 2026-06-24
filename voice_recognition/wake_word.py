"""Wake word detection, with fuzzy matching for common STT misrecognitions
(e.g. "사비스", "자빗스", "자비스스", "자비스요" for "자비스").

A generic Levenshtein-distance-1 match over 3-character windows was tried
first but rejected: "자비스" is short enough that ANY single-character
substitution is within distance 1 of real, unrelated words -- "자비를"
(object form of "자비", mercy), "비스킷" (biscuit), etc. all matched. Instead,
each syllable position has its own small set of accepted characters, which
covers the specific confusions Whisper actually makes (자/사, 비/빗) without
opening the door to arbitrary one-character matches.
"""

WAKE_WORD = "자비스"
_POSITION_VARIANTS = [
    {"자", "사"},  # 1st syllable: 자/사 (voiced/unvoiced confusion)
    {"비", "빗"},  # 2nd syllable: 비/빗
    {"스"},  # 3rd syllable: fixed -- no substitution here keeps false positives low
]
_BOUNDARY_CHARS = " ,.!?~"


def _is_core_match(window: str) -> bool:
    return len(window) == 3 and all(ch in variants for ch, variants in zip(window, _POSITION_VARIANTS))


def _find_wake_word_span(text: str) -> tuple[int, int] | None:
    """Return the (start, end) span of a fuzzy wake-word match in `text`, or
    None. If a core match is immediately followed by one more non-boundary
    character (e.g. the extra "스" in "자비스스", or "요" in "자비스요"),
    that character is absorbed into the span too."""
    n = len(WAKE_WORD)
    for start in range(len(text) - n + 1):
        if _is_core_match(text[start : start + n]):
            end = start + n
            if end < len(text) and text[end] not in _BOUNDARY_CHARS:
                end += 1
            return start, end
    return None


def contains_wake_word(text: str) -> bool:
    return _find_wake_word_span(text) is not None


def extract_command(text: str) -> str:
    """Return whatever follows the wake word in `text` (e.g. "자비스 크롬 열어"
    -> "크롬 열어"), with leading punctuation/whitespace stripped. Empty
    string if the wake word is the entire utterance, or isn't found."""
    span = _find_wake_word_span(text)
    if span is None:
        return ""
    return text[span[1]:].strip(" ,.!?~")
