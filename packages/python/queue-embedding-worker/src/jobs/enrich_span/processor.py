from jobs.enrich_span.types import EnrichSpanPayload, EnrichSpanResult
from shared.errors.base import ValidationError
from shared.utils.hash import stable_embedding_key


class InvalidDimensionsError(ValidationError):
    pass


class InvalidPayloadError(ValidationError):
    pass


def process(payload: EnrichSpanPayload, dimensions: int) -> EnrichSpanResult:
    if dimensions <= 0:
        raise InvalidDimensionsError("dimensions must be greater than zero")
    if not payload.text.strip():
        raise InvalidPayloadError("text must be non-empty")

    return EnrichSpanResult(
        trace_id=payload.trace_id,
        span_id=payload.span_id,
        embedding_key=stable_embedding_key(payload.trace_id, payload.span_id, payload.text),
        dimensions=dimensions,
        model=payload.model,
    )
