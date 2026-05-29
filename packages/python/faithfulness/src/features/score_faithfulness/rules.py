from __future__ import annotations

from features.score_faithfulness.types import FaithfulnessInput

MIN_CONTEXT_CHARS: int = 50
MIN_COMPLETION_TOKENS: int = 10
MIN_SENTENCE_WORDS: int = 5
TEMPERATURE: float = 1.5
CONTEXT_TOKEN_LIMIT: int = 512
CONTEXT_CHUNK_TOKENS: int = 400
NLI_BATCH_SIZE: int = 8
BLOCKED_FINISH_REASONS: frozenset[str] = frozenset({"content_filter"})

_LABEL_NAMES: tuple[str, str, str] = ("entailment", "neutral", "contradiction")


def label_from_probs(probs: tuple[float, float, float]) -> str:
    return _LABEL_NAMES[probs.index(max(probs))]


def should_skip(input: FaithfulnessInput) -> tuple[bool, str | None]:
    if input.finish_reason in BLOCKED_FINISH_REASONS:
        return True, "finish_reason_blocked"
    if input.rag_context is None:
        return True, "rag_context_null"
    if len(input.rag_context) < MIN_CONTEXT_CHARS:
        return True, "rag_context_too_short"
    if input.completion_tokens < MIN_COMPLETION_TOKENS:
        return True, "completion_tokens_too_few"
    return False, None


def split_context_into_chunks(context: str) -> list[str]:
    words = context.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + CONTEXT_CHUNK_TOKENS
        chunks.append(" ".join(words[start:end]))
        start = end
    return chunks


def context_exceeds_limit(context: str) -> bool:
    return len(context.split()) > CONTEXT_TOKEN_LIMIT
