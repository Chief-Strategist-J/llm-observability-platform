import pytest

from jobs.enrich_span.processor import InvalidDimensionsError, InvalidPayloadError, process
from jobs.enrich_span.types import EnrichSpanPayload


@pytest.mark.parametrize(
    "text",
    ["a", "hello world", "🔥 unicode", "line1\nline2", "x" * 500],
)
def test_process_deterministic_for_same_payload(text):
    payload = EnrichSpanPayload("trace-a", "span-b", text, "text-embedding-3-small")
    assert process(payload, 256).embedding_key == process(payload, 256).embedding_key


@pytest.mark.parametrize(
    "left,right",
    [
        ("a", "b"),
        ("hello", "hello "),
        ("X", "x"),
        ("1", "2"),
        ("alpha", "beta"),
    ],
)
def test_process_key_changes_for_different_text(left, right):
    p1 = EnrichSpanPayload("trace-a", "span-b", left, "text-embedding-3-small")
    p2 = EnrichSpanPayload("trace-a", "span-b", right, "text-embedding-3-small")
    assert process(p1, 256).embedding_key != process(p2, 256).embedding_key


@pytest.mark.parametrize("dimensions", [0, -1, -10])
def test_process_rejects_non_positive_dimensions(dimensions):
    payload = EnrichSpanPayload("trace-a", "span-b", "text-a", "text-embedding-3-small")
    with pytest.raises(InvalidDimensionsError):
        process(payload, dimensions)


@pytest.mark.parametrize("text", ["", " ", "\n", "\t", "   \n"])
def test_process_rejects_empty_text(text):
    payload = EnrichSpanPayload("trace-a", "span-b", text, "text-embedding-3-small")
    with pytest.raises(InvalidPayloadError):
        process(payload, 128)


def test_process_copies_trace_and_span():
    payload = EnrichSpanPayload("trace-xyz", "span-xyz", "text", "text-embedding-3-small")
    result = process(payload, 128)
    assert result.trace_id == "trace-xyz"
    assert result.span_id == "span-xyz"
