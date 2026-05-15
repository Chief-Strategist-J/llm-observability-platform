from jobs.enrich_span.processor import process
from jobs.enrich_span.types import EnrichSpanPayload


def handler(message: dict, *, dimensions: int) -> dict:
    payload = EnrichSpanPayload(**message)
    return process(payload, dimensions).__dict__
