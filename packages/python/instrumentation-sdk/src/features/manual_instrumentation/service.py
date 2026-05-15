import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from ..spans.index import LLMSpan, FinishReason, TokenCountMethod, Environment
from ..spans.globals import get_reporter

class LLMSpanContext:
    def __init__(self, **kwargs: Any):
        self._span_id = uuid.uuid4()
        self._start_time = time.perf_counter()
        self._data: Dict[str, Any] = {
            "span_id": self._span_id,
            "timestamp_utc": datetime.now(timezone.utc),
            "status": "success",
            **kwargs
        }

    def set_metadata(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __enter__(self) -> 'LLMSpanContext':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._finish(exc_type)
        reporter = get_reporter()
        reporter.report(self._data)

    async def __aenter__(self) -> 'LLMSpanContext':
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._finish(exc_type)
        reporter = get_reporter()
        await reporter.report_async(self._data)

    def _finish(self, exc_type: Any) -> None:
        latency_ms = int((time.perf_counter() - self._start_time) * 1000)
        self._data["latency_ms_total"] = latency_ms
        if exc_type:
            self._data["status"] = "error"

def llm_span(**kwargs: Any) -> LLMSpanContext:
    return LLMSpanContext(**kwargs)
