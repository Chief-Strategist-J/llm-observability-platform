from typing import Callable, Any, Dict, Optional
import time
import json
import threading
import logging
from src.infra.messaging.middleware.pipeline import ConsumeCtx
from src.infra.messaging.tracing.messaging_tracer import messaging_tracer

logger = logging.getLogger("kafka.consumer.middleware")

def with_tracing_consumer(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
    event_name = ctx.metadata.get("event_name", "LLMSpan")
    with messaging_tracer.start_consumer_span(
        topic=ctx.topic,
        event_name=event_name,
        headers=ctx.headers,
    ) as span:
        return next_fn(ctx)

def with_deserialization(
    decoder_fn: Optional[Callable[[bytes], Any]] = None,
) -> Callable[[ConsumeCtx, Callable[[ConsumeCtx], Any]], Any]:
    decode = decoder_fn or (lambda raw: json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw)

    def _middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
        raw_val = getattr(ctx.raw_message, "value", None)
        if raw_val is None:
            ctx.payload = None
            return next_fn(ctx)

        try:
            ctx.payload = decode(raw_val)
        except Exception as err:
            logger.error(f"Deserialization error on topic {ctx.topic} at offset {ctx.offset}: {err}")
            raise ValueError(f"Deserialization failed for message: {err}") from err

        return next_fn(ctx)

    return _middleware

def with_retry_count_header(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
    retry_header = ctx.headers.get("x-retry-count", "0")
    try:
        ctx.attempt = int(retry_header)
    except ValueError:
        ctx.attempt = 0

    return next_fn(ctx)

def with_dlq_on_failure(
    max_attempts: int = 3,
    dlq_publisher_fn: Optional[Callable[[ConsumeCtx, Exception], None]] = None,
) -> Callable[[ConsumeCtx, Callable[[ConsumeCtx], Any]], Any]:

    def _middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
        try:
            return next_fn(ctx)
        except Exception as err:
            ctx.attempt += 1
            logger.error(
                f"Processing failed on {ctx.topic} (attempt {ctx.attempt}/{max_attempts}): {err}"
            )
            if ctx.attempt >= max_attempts:
                if dlq_publisher_fn:
                    logger.warning(f"Routing message to DLQ topic for {ctx.topic} @ offset {ctx.offset}")
                    dlq_publisher_fn(ctx, err)
                    return None
                raise err
            raise err

    return _middleware

def with_tenant_context(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
    tenant_id = ctx.headers.get("tenant_id") or ctx.headers.get("x-tenant-id")
    if not tenant_id and isinstance(ctx.payload, dict):
        tenant_id = ctx.payload.get("org_id") or ctx.payload.get("tenant_id")

    if not tenant_id:
        raise ValueError(f"Security violation: Missing tenant_id in message headers on topic {ctx.topic}")

    ctx.tenant_id = tenant_id
    return next_fn(ctx)

class SemaphoreBoundedWorker:
    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = threading.Semaphore(max_concurrent)

def with_concurrency_limit(
    max_concurrent: int = 10,
) -> Callable[[ConsumeCtx, Callable[[ConsumeCtx], Any]], Any]:
    sem = threading.Semaphore(max_concurrent)

    def _middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
        with sem:
            return next_fn(ctx)

    return _middleware

def with_heartbeat_during_processing(
    interval_sec: float = 3.0,
) -> Callable[[ConsumeCtx, Callable[[ConsumeCtx], Any]], Any]:

    def _middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], Any]) -> Any:
        stop_event = threading.Event()

        def _heartbeat_loop():
            while not stop_event.wait(interval_sec):
                if ctx.heartbeat_fn:
                    try:
                        ctx.heartbeat_fn()
                    except Exception:
                        pass

        heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        try:
            return next_fn(ctx)
        finally:
            stop_event.set()
            heartbeat_thread.join(timeout=1.0)

    return _middleware
