from dataclasses import dataclass


@dataclass(frozen=True)
class EnrichSpanPayload:
    trace_id: str
    span_id: str
    text: str
    model: str


@dataclass(frozen=True)
class EnrichSpanResult:
    trace_id: str
    span_id: str
    embedding_key: str
    dimensions: int
    model: str
