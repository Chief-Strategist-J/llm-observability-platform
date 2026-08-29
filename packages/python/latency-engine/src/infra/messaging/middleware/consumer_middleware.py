from __future__ import annotations

import json
import logging
from typing import Callable
from infra.messaging.middleware.pipeline import ConsumeCtx

logger = logging.getLogger(__name__)


def deserialization_middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], None]) -> None:
    if ctx.raw_value:
        try:
            ctx.payload = json.loads(ctx.raw_value.decode("utf-8"))
        except Exception as exc:
            logger.error("Deserialization failed for topic %s: %s", ctx.topic, exc)
            ctx.error = exc
            ctx.aborted = True
            return
    next_fn(ctx)


def tenant_isolation_middleware(ctx: ConsumeCtx, next_fn: Callable[[ConsumeCtx], None]) -> None:
    if isinstance(ctx.headers, dict) and "tenant_id" in ctx.headers:
        val = ctx.headers["tenant_id"]
        ctx.tenant_id = val.decode("utf-8") if isinstance(val, bytes) else str(val)
    elif isinstance(ctx.payload, dict) and "tenant_id" in ctx.payload:
        ctx.tenant_id = str(ctx.payload["tenant_id"])
    next_fn(ctx)
