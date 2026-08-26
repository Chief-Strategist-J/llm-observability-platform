import json
from typing import Dict, Any, Callable
from src.features.spans.types import LLMSpan
from src.infra.messaging.cqrs.projection_store import projection_store

class SpanIngestionConsumerHandler:
    def __init__(self, projection_store_instance=projection_store):
        self.projection_store = projection_store_instance

    def process_message(self, message: Any) -> Dict[str, Any]:
        raw_val = getattr(message, "value", None)
        payload = json.loads(raw_val.decode("utf-8")) if isinstance(raw_val, bytes) else (raw_val or {})
        span = LLMSpan(**payload)
        
        session_id = span.session_id or str(span.trace_id or span.span_id)
        self.projection_store.apply_event(
            event_type="LLMSpanRecorded",
            aggregate_id=session_id,
            payload=span.model_dump(mode="json")
        )
        return {"status": "processed", "span_id": str(span.span_id), "session_id": session_id}

span_consumer_handler = SpanIngestionConsumerHandler()
