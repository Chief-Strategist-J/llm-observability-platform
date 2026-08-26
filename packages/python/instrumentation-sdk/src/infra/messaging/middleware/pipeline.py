from typing import Callable, Any, List, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field

T = TypeVar("T")

@dataclass
class ProduceCtx(Generic[T]):
    topic: str
    key: str
    payload: T
    headers: Dict[str, str] = field(default_factory=dict)
    partition: Optional[int] = None
    tenant_id: str = "default"
    correlation_id: str = ""
    deadline: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConsumeCtx(Generic[T]):
    topic: str
    partition: int
    offset: str
    raw_message: Any
    payload: Optional[T] = None
    headers: Dict[str, str] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    attempt: int = 1
    heartbeat_fn: Optional[Callable[[], None]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

ProducerMiddleware = Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]
ConsumerMiddleware = Callable[[ConsumeCtx, Callable[[ConsumeCtx], Any]], Any]

def compose(*middlewares: Callable) -> Callable:
    def _composed(final_fn: Callable) -> Callable:
        fn = final_fn
        for mw in reversed(middlewares):
            def _next(current_mw=mw, next_fn=fn):
                return lambda ctx: current_mw(ctx, next_fn)
            fn = _next()
        return fn
    return _composed

class ProducerMiddlewarePipeline:
    def __init__(self, middlewares: List[ProducerMiddleware]) -> None:
        self.middlewares = middlewares

    def execute(self, ctx: ProduceCtx, target_produce_fn: Callable[[ProduceCtx], None]) -> None:
        composed_chain = compose(*self.middlewares)(target_produce_fn)
        composed_chain(ctx)

class ConsumerMiddlewarePipeline:
    def __init__(self, middlewares: List[ConsumerMiddleware]) -> None:
        self.middlewares = middlewares

    def execute(self, ctx: ConsumeCtx, target_handler_fn: Callable[[ConsumeCtx], Any]) -> Any:
        composed_chain = compose(*self.middlewares)(target_handler_fn)
        return composed_chain(ctx)
