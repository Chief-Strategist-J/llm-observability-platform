from __future__ import annotations
from handlers.span_quality.types import SampledSpan
from handlers.span_quality.prompt_type_detector import detect_prompt_type


def _make_span(**kwargs) -> SampledSpan:
    defaults = dict(
        span_id="s1", trace_id="t1", model="gpt-4", endpoint="/v1/chat",
        prompt_text="hello world", response_text="Hello! How can I help you today with a longer response?",
        completion_tokens=20, finish_reason="stop",
    )
    defaults.update(kwargs)
    return SampledSpan(**defaults)


def test_detect_rag_when_rag_context_present():
    span = _make_span(rag_context="some retrieved doc", prompt_text="```python\ncode```")
    # rag takes priority over code blocks
    assert detect_prompt_type(span) == "rag"


def test_detect_code_when_backticks_in_prompt():
    span = _make_span(prompt_text="```python\nprint('hello')\n```")
    assert detect_prompt_type(span) == "code"


def test_detect_classification_when_short_response():
    span = _make_span(response_text="yes")
    assert detect_prompt_type(span) == "classification"


def test_detect_chat_as_default():
    span = _make_span()
    assert detect_prompt_type(span) == "chat"
