from __future__ import annotations

try:
    from langdetect import detect as _detect  # type: ignore[import-untyped]
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


def detect_language(response_text: str) -> str:
    """
    F-Q-03: Detect language of response using langdetect on first 500 characters.
    Returns ISO 639-1 language code. Falls back to 'en' if detection fails or lib is unavailable.
    Non-English responses get flagged for separate baseline tracking (see handler).
    """
    if not _LANGDETECT_AVAILABLE or not response_text:
        return "en"

    sample = response_text[:500]
    try:
        return str(_detect(sample))
    except Exception:
        return "en"
