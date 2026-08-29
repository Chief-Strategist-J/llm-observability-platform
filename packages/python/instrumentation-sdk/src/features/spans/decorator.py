import functools
import time
import uuid
import asyncio
import inspect
from typing import Optional, Callable, Any
from datetime import datetime, timezone
from .globals import get_reporter
from ..metrics.index import record_span_metrics, get_current_prices_ref
from ..deterministic_sampling.index import should_sample
from ...infra.tracing.tracer import get_tracer, init_tracer

def llm_observe(service: str, endpoint: str):
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                init_tracer(service)
                tracer = get_tracer()
                start_time = time.perf_counter()
                start_timestamp = datetime.now(timezone.utc).isoformat()
                prices_ref = get_current_prices_ref()
                with tracer.start_as_current_span(f"{service}:{endpoint}") as otel_span:
                    sc = otel_span.get_span_context()
                    trace_id_str = f"{sc.trace_id:032x}" if sc and sc.trace_id else str(uuid.uuid4()).replace("-", "")
                    span_id_str = f"{sc.span_id:016x}" if sc and sc.span_id else str(uuid.uuid4())[:16]
                    otel_span.set_attribute("service.name", service)
                    otel_span.set_attribute("endpoint", endpoint)
                    try:
                        result = await func(*args, **kwargs)
                        status = "success"
                        return result
                    except Exception as e:
                        status = "error"
                        otel_span.record_exception(e)
                        raise e
                    finally:
                        latency_ms = int((time.perf_counter() - start_time) * 1000)
                        span_data = {
                            "span_id": span_id_str,
                            "trace_id": trace_id_str,
                            "traceparent": f"00-{trace_id_str}-{span_id_str}-01",
                            "service_name": service,
                            "endpoint": endpoint,
                            "latency_ms_total": latency_ms,
                            "timestamp_utc": start_timestamp,
                            "status": status,
                            "is_sampled": should_sample(span_id_str),
                            "_prices_ref": prices_ref,
                        }
                        from ..minilm_embedding.index import enrich_and_report_span_async
                        await enrich_and_report_span_async(span_data)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                init_tracer(service)
                tracer = get_tracer()
                start_time = time.perf_counter()
                start_timestamp = datetime.now(timezone.utc).isoformat()
                prices_ref = get_current_prices_ref()
                with tracer.start_as_current_span(f"{service}:{endpoint}") as otel_span:
                    sc = otel_span.get_span_context()
                    trace_id_str = f"{sc.trace_id:032x}" if sc and sc.trace_id else str(uuid.uuid4()).replace("-", "")
                    span_id_str = f"{sc.span_id:016x}" if sc and sc.span_id else str(uuid.uuid4())[:16]
                    otel_span.set_attribute("service.name", service)
                    otel_span.set_attribute("endpoint", endpoint)
                    try:
                        result = func(*args, **kwargs)
                        status = "success"
                        return result
                    except Exception as e:
                        status = "error"
                        otel_span.record_exception(e)
                        raise e
                    finally:
                        latency_ms = int((time.perf_counter() - start_time) * 1000)
                        span_data = {
                            "span_id": span_id_str,
                            "trace_id": trace_id_str,
                            "traceparent": f"00-{trace_id_str}-{span_id_str}-01",
                            "service_name": service,
                            "endpoint": endpoint,
                            "latency_ms_total": latency_ms,
                            "timestamp_utc": start_timestamp,
                            "status": status,
                            "is_sampled": should_sample(span_id_str),
                            "_prices_ref": prices_ref,
                        }
                        from ..minilm_embedding.index import enrich_and_report_span
                        enrich_and_report_span(span_data)
            return sync_wrapper
    return decorator
