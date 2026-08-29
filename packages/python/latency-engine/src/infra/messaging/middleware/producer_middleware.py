from __future__ import annotations

import json
import logging
from typing import Callable
from infra.messaging.middleware.pipeline import ProduceCtx

logger = logging.getLogger(__name__)


def serialization_middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
    if isinstance(ctx.value, (dict, list)):
        ctx.value = json.dumps(ctx.value).encode("utf-8")
    elif isinstance(ctx.value, str):
        ctx.value = ctx.value.encode("utf-8")
    next_fn(ctx)


def partition_key_middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
    if not ctx.key and isinstance(ctx.value, bytes):
        try:
            val_json = json.loads(ctx.value.decode("utf-8"))
            if isinstance(val_json, dict) and "model" in val_json:
                ctx.key = str(val_json["model"]).encode("utf-8")
        except Exception:
            pass
    next_fn(ctx)
