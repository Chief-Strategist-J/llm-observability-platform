from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

Ctx = TypeVar("Ctx")
Res = TypeVar("Res")

@dataclass
class ProduceCtx:
    topic: str
    value: Any
    key: str | bytes | None = None
    headers: dict[str, str | bytes] = field(default_factory=dict)
    partition: int = -1
    tenant_id: str = "default"
    correlation_id: str = ""
    deadline_ms: float = 0.0
    aborted: bool = False
    error: Exception | None = None

@dataclass
class ConsumeCtx:
    topic: str
    partition: int
    offset: int
    raw_key: bytes | None
    raw_value: bytes | None
    headers: dict[str, str] = field(default_factory=dict)
    payload: Any = None
    tenant_id: str | None = None
    correlation_id: str = ""
    retry_count: int = 0
    aborted: bool = False
    error: Exception | None = None

NextFn = Callable[[Ctx], Res]
MiddlewareFn = Callable[[NextFn[Ctx, Res]], NextFn[Ctx, Res]]

def compose(*middlewares: MiddlewareFn[Ctx, Res]) -> Callable[[NextFn[Ctx, Res]], NextFn[Ctx, Res]]:
    def decorator(target: NextFn[Ctx, Res]) -> NextFn[Ctx, Res]:
        fn = target
        for mw in reversed(middlewares):
            fn = mw(fn)
        return fn
    return decorator
