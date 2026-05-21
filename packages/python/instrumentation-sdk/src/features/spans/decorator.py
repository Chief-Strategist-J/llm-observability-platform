import functools
import time
import uuid
import asyncio
import inspect
from typing import Optional, Callable, Any
from datetime import datetime, timezone
from .globals import get_reporter
from ..metrics.index import record_span_metrics
from ..deterministic_sampling.index import should_sample

def llm_observe(service: str, endpoint: str):
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_id = str(uuid.uuid4())
                start_time = time.perf_counter()
                start_timestamp = datetime.now(timezone.utc).isoformat()
                
                try:
                    result = await func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise e
                finally:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    span_data = {
                        "span_id": span_id,
                        "service_name": service,
                        "endpoint": endpoint,
                        "latency_ms_total": latency_ms,
                        "timestamp_utc": start_timestamp,
                        "status": status,
                        "is_sampled": should_sample(span_id)
                    }
                    reporter = get_reporter()
                    record_span_metrics(span_data)
                    await reporter.report_async(span_data)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_id = str(uuid.uuid4())
                start_time = time.perf_counter()
                start_timestamp = datetime.now(timezone.utc).isoformat()
                
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise e
                finally:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    span_data = {
                        "span_id": span_id,
                        "service_name": service,
                        "endpoint": endpoint,
                        "latency_ms_total": latency_ms,
                        "timestamp_utc": start_timestamp,
                        "status": status,
                        "is_sampled": should_sample(span_id)
                    }
                    reporter = get_reporter()
                    record_span_metrics(span_data)
                    reporter.report(span_data)
            return sync_wrapper
    return decorator
