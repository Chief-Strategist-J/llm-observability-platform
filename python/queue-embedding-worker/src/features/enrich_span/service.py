from jobs.enrich_span.types import EnrichSpanPayload
from shared.ports.embedding_provider import EmbeddingRequest
from shared.di.providers import resolve_embedding_provider
from shared.errors.base import ValidationError



def enrich_span(payload: dict, *, dimensions: int, provider_name: str = "cloudflare") -> dict:
    parsed = EnrichSpanPayload(**payload)
    if dimensions <= 0:
        raise ValidationError("dimensions must be greater than zero")
    if not parsed.text.strip():
        raise ValidationError("text must be non-empty")

    provider = resolve_embedding_provider(provider_name)
    resp = provider.create_embedding(
        EmbeddingRequest(
            text=parsed.text,
            model=parsed.model,
            trace_id=parsed.trace_id,
            span_id=parsed.span_id,
        ),
        dimensions=dimensions,
    )
    return {
        "trace_id": parsed.trace_id,
        "span_id": parsed.span_id,
        "embedding_key": resp.embedding_key,
        "dimensions": resp.dimensions,
        "model": parsed.model,
        "provider": resp.provider,
    }
