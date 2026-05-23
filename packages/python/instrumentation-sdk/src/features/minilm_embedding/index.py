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
    trace_id = span_data.get("trace_id")
    if trace_id:
        from ..spans.fallback_tracker import track_fallback
        retry_count, attempted_models = track_fallback(trace_id, span_data.get("model"))
        span_data["attempted_models"] = attempted_models
        span_data["retry_count"] = max(span_data.get("retry_count", 0), retry_count)
    elif span_data.get("model") and not span_data.get("attempted_models"):
        span_data["attempted_models"] = [span_data.get("model")]

    record_span_metrics(span_data)
    if trace_id:
        from ..spans.tool_call_tracker import track_tool_call
        track_tool_call(trace_id, span_data.get("span_id"), span_data.get("cost_usd_micro", 0))

    if not span_data.get("is_sampled", False) or span_data.get("pii_detected", False) or not span_data.get("prompt"):
        reporter = get_reporter()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(reporter.report_async(span_data))
        except RuntimeError:
            reporter.report(span_data)
    else:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_async_enrich_and_report(span_data))
        except RuntimeError:
            threading.Thread(target=_sync_enrich_and_report, args=(span_data,)).start()

    finish_reason = span_data.get("finish_reason")
    is_tool_call = False
    if finish_reason:
        if isinstance(finish_reason, str):
            if finish_reason.lower() == "tool_calls" or finish_reason.split("_")[-1].lower() == "tool_calls":
                is_tool_call = True
        elif hasattr(finish_reason, "value"):
            val = str(finish_reason.value)
            if val.lower() == "tool_calls" or val.split("_")[-1].lower() == "tool_calls":
                is_tool_call = True

    if is_tool_call:
        import uuid
        from datetime import datetime, timezone
        from ..spans.types import FinishReason
        from ..spans.tool_call_tracker import track_tool_call
        intermediate_span = {
            "span_id": uuid.uuid4(),
            "trace_id": span_data.get("trace_id"),
            "parent_span_id": span_data.get("span_id"),
            "schema_version": 1,
            "model": span_data.get("model", "unknown"),
            "provider": span_data.get("provider", "unknown"),
            "service_name": span_data.get("service_name", "unknown"),
            "endpoint": span_data.get("endpoint", "unknown"),
            "environment": span_data.get("environment", "unspecified"),
            "user_id": span_data.get("user_id"),
            "session_id": span_data.get("session_id"),
            "prompt_tokens": 1,
            "completion_tokens": 0,
            "latency_ms_total": 1,
            "finish_reason": FinishReason.STOP,
            "cost_usd_micro": 0,
            "price_version": span_data.get("price_version", "unknown"),
            "timestamp_utc": datetime.now(timezone.utc),
            "status": "success",
            "is_sampled": span_data.get("is_sampled", False),
        }
        if intermediate_span.get("trace_id"):
            track_tool_call(intermediate_span["trace_id"], intermediate_span["span_id"], 0)
        reporter = get_reporter()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(reporter.report_async(intermediate_span))
        except RuntimeError:
            reporter.report(intermediate_span)

async def enrich_and_report_span_async(span_data: Dict[str, Any]) -> None:
    trace_id = span_data.get("trace_id")
    if trace_id:
        from ..spans.fallback_tracker import track_fallback
        retry_count, attempted_models = track_fallback(trace_id, span_data.get("model"))
        span_data["attempted_models"] = attempted_models
        span_data["retry_count"] = max(span_data.get("retry_count", 0), retry_count)
    elif span_data.get("model") and not span_data.get("attempted_models"):
        span_data["attempted_models"] = [span_data.get("model")]

    record_span_metrics(span_data)
    if trace_id:
        from ..spans.tool_call_tracker import track_tool_call
        track_tool_call(trace_id, span_data.get("span_id"), span_data.get("cost_usd_micro", 0))

    if not span_data.get("is_sampled", False) or span_data.get("pii_detected", False) or not span_data.get("prompt"):
        reporter = get_reporter()
        await reporter.report_async(span_data)
    else:
        prompt = span_data.get("prompt")
        if prompt:
            embedding = await _SERVICE.get_embedding(prompt)
            span_data["prompt_embedding"] = embedding
        reporter = get_reporter()
        await reporter.report_async(span_data)

    finish_reason = span_data.get("finish_reason")
    is_tool_call = False
    if finish_reason:
        if isinstance(finish_reason, str):
            if finish_reason.lower() == "tool_calls" or finish_reason.split("_")[-1].lower() == "tool_calls":
                is_tool_call = True
        elif hasattr(finish_reason, "value"):
            val = str(finish_reason.value)
            if val.lower() == "tool_calls" or val.split("_")[-1].lower() == "tool_calls":
                is_tool_call = True

    if is_tool_call:
        import uuid
        from datetime import datetime, timezone
        from ..spans.types import FinishReason
        from ..spans.tool_call_tracker import track_tool_call
        intermediate_span = {
            "span_id": uuid.uuid4(),
            "trace_id": span_data.get("trace_id"),
            "parent_span_id": span_data.get("span_id"),
            "schema_version": 1,
            "model": span_data.get("model", "unknown"),
            "provider": span_data.get("provider", "unknown"),
            "service_name": span_data.get("service_name", "unknown"),
            "endpoint": span_data.get("endpoint", "unknown"),
            "environment": span_data.get("environment", "unspecified"),
            "user_id": span_data.get("user_id"),
            "session_id": span_data.get("session_id"),
            "prompt_tokens": 1,
            "completion_tokens": 0,
            "latency_ms_total": 1,
            "finish_reason": FinishReason.STOP,
            "cost_usd_micro": 0,
            "price_version": span_data.get("price_version", "unknown"),
            "timestamp_utc": datetime.now(timezone.utc),
            "status": "success",
            "is_sampled": span_data.get("is_sampled", False),
        }
        if intermediate_span.get("trace_id"):
            track_tool_call(intermediate_span["trace_id"], intermediate_span["span_id"], 0)
        reporter = get_reporter()
        await reporter.report_async(intermediate_span)

