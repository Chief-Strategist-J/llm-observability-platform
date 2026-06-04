from __future__ import annotations
from handlers.span_quality.types import PromptType, SampledSpan


def detect_prompt_type(span: SampledSpan) -> PromptType:
    """
    F-Q-02: Lightweight rule-based prompt type classifier.
    Order of evaluation matters — rag overrides code, code overrides classification.
    Default is 'chat'.
    """
    text = span.prompt_text

    if span.rag_context is not None:
        return "rag"

    if "```" in text:
        return "code"

    words = span.response_text.strip().split()
    if len(words) <= 3:
        return "classification"

    return "chat"
