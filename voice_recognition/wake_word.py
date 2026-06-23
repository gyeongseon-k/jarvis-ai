"""Wake word detection."""

WAKE_WORD = "자비스"


def contains_wake_word(text: str) -> bool:
    return WAKE_WORD in text.replace(" ", "")
