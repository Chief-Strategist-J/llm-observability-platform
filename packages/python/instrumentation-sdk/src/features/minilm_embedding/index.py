import os
import asyncio
import threading
from typing import Any, Dict, Optional
from ..spans.globals import get_reporter
from ..metrics.index import record_span_metrics
from .service import MiniLMEmbeddingService
from .infra.adapters.http_embedding_client_adapter import HttpEmbeddingClientAdapter

_ENDPOINT = os.getenv("EMBEDDING_WORKER_URL", "http://localhost:8000")
_ADAPTER = HttpEmbeddingClientAdapter(f"{_ENDPOINT.rstrip('/')}/embed")
_SERVICE = MiniLMEmbeddingService(_ADAPTER)

async def get_embedding(text: str) -> Optional[list[float]]:
    return await _SERVICE.get_embedding(text)

async def _async_enrich_and_report(span_data: Dict[str, Any]) -> None:
    prompt = span_data.get("prompt")
    if prompt:
        embedding = await _SERVICE.get_embedding(prompt)
        span_data["prompt_embedding"] = embedding
    reporter = get_reporter()
    try:
        await reporter.report_async(span_data)
    except Exception:
        try:
            reporter.report(span_data)
        except Exception:
            pass

def _sync_enrich_and_report(span_data: Dict[str, Any]) -> None:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_enrich_and_report(span_data))
        loop.close()
    except Exception:
        pass

def enrich_and_report_span(span_data: Dict[str, Any]) -> None:
    record_span_metrics(span_data)
    if not span_data.get("is_sampled", False) or span_data.get("pii_detected", False) or not span_data.get("prompt"):
        reporter = get_reporter()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(reporter.report_async(span_data))
        except RuntimeError:
            reporter.report(span_data)
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_async_enrich_and_report(span_data))
    except RuntimeError:
        threading.Thread(target=_sync_enrich_and_report, args=(span_data,)).start()

async def enrich_and_report_span_async(span_data: Dict[str, Any]) -> None:
    record_span_metrics(span_data)
    if not span_data.get("is_sampled", False) or span_data.get("pii_detected", False) or not span_data.get("prompt"):
        reporter = get_reporter()
        await reporter.report_async(span_data)
        return
    prompt = span_data.get("prompt")
    if prompt:
        embedding = await _SERVICE.get_embedding(prompt)
        span_data["prompt_embedding"] = embedding
    reporter = get_reporter()
    await reporter.report_async(span_data)
