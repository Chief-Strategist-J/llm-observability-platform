from __future__ import annotations
import json
import logging
from typing import Callable
from opentelemetry.trace import Status, StatusCode
from infra.messaging.middleware.pipeline import ProduceCtx, NextFn
from shared.constants.kafka_constants import kafka_constants
from shared.tracing.tracer import get_tracer

logger = logging.getLogger(__name__)

def tracing_producer_middleware(next_fn: NextFn[ProduceCtx, None]) -> NextFn[ProduceCtx, None]:
    def wrapper(ctx: ProduceCtx) -> None:
        tracer = get_tracer()
        span_name = f"kafka.produce.{ctx.topic}"
        with tracer.start_as_current_span(span_name) as span:
            span_ctx = span.get_span_context()
            if span_ctx and span_ctx.trace_id:
                trace_id_hex = f"{span_ctx.trace_id:032x}"
                span_id_hex = f"{span_ctx.span_id:016x}"
                traceparent_val = f"00-{trace_id_hex}-{span_id_hex}-01"
                ctx.headers[kafka_constants.HEADER_TRACEPARENT] = traceparent_val
                ctx.headers[kafka_constants.HEADER_X_TRACE_ID] = trace_id_hex
                ctx.correlation_id = trace_id_hex

            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination", ctx.topic)
            span.set_attribute("messaging.destination_kind", "topic")
            
            try:
                next_fn(ctx)
                span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
    return wrapper

def serialization_middleware(next_fn: NextFn[ProduceCtx, None]) -> NextFn[ProduceCtx, None]:
    def wrapper(ctx: ProduceCtx) -> None:
        if isinstance(ctx.value, (dict, list)):
            ctx.value = json.dumps(ctx.value).encode("utf-8")
        elif isinstance(ctx.value, str):
            ctx.value = ctx.value.encode("utf-8")
        next_fn(ctx)
    return wrapper

def partition_key_middleware(next_fn: NextFn[ProduceCtx, None]) -> NextFn[ProduceCtx, None]:
    def wrapper(ctx: ProduceCtx) -> None:
        if not ctx.key and isinstance(ctx.value, bytes):
            try:
                val_json = json.loads(ctx.value.decode("utf-8"))
                if isinstance(val_json, dict) and "model" in val_json:
                    ctx.key = str(val_json["model"]).encode("utf-8")
            except Exception:
                pass
        next_fn(ctx)
    return wrapper
