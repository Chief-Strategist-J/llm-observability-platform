from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass
class ProduceCtx:
    topic: str
    value: Any
    key: str | bytes | None = None
    headers: dict[str, str | bytes] = field(default_factory=dict)
    partition: int = -1
    aborted: bool = False
    error: Exception | None = None


@dataclass
class ConsumeCtx:
    topic: str
    partition: int
    offset: int
    raw_key: bytes | None
    raw_value: bytes | None
    headers: dict[str, bytes] = field(default_factory=dict)
    payload: Any = None
    tenant_id: str | None = None
    retry_count: int = 0
    aborted: bool = False
    error: Exception | None = None


MiddlewareFn = Callable[[T, Callable[[T], None]], None]


def compose(middlewares: list[MiddlewareFn[T]], target: Callable[[T], None]) -> Callable[[T], None]:
    def _composed(ctx: T) -> None:
        idx = 0

        def _next(curr_ctx: T) -> None:
            nonlocal idx
            if idx < len(middlewares):
                curr_mw = middlewares[idx]
                idx += 1
                curr_mw(curr_ctx, _next)
            else:
                target(curr_ctx)

        _next(ctx)

    return _composed
