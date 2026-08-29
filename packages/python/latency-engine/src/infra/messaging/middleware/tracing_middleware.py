from __future__ import annotations

from typing import Callable
from infra.messaging.middleware.pipeline import ConsumeCtx, ProduceCtx
from infra.messaging.tracing.context_propagation import extract_trace_context, inject_trace_context
from shared.tracing.tracer import get_tracer


def tracing_producer_middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
    tracer = get_tracer()
    with tracer.start_as_current_span(f"kafka.produce.{ctx.topic}") as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination", ctx.topic)
        ctx.headers.update(inject_trace_context())
        next_fn(ctx)


def tracing_consumer_middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], None]) -> None:
    tracer = get_tracer()
    parent_ctx = extract_trace_context(ctx.headers)
    with tracer.start_as_current_span(f"kafka.consume.{ctx.topic}", context=parent_ctx) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination", ctx.topic)
        span.set_attribute("messaging.kafka.partition", ctx.partition)
        span.set_attribute("messaging.kafka.offset", ctx.offset)
        next_fn(ctx)
