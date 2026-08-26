from typing import Callable, Any, List

ProducerMiddleware = Callable[[str, Any, Any, Callable], None]
ConsumerMiddleware = Callable[[Any, Callable], Any]

class ProducerMiddlewarePipeline:
    def __init__(self, middlewares: List[ProducerMiddleware]) -> None:
        self.middlewares = middlewares

    def execute(self, topic: str, key: Any, value: Any, target_produce_fn: Callable) -> None:
        def _build_chain(index: int):
            if index >= len(self.middlewares):
                return lambda t, k, v: target_produce_fn(t, k, v)
            mw = self.middlewares[index]
            next_fn = _build_chain(index + 1)
            return lambda t, k, v: mw(t, k, v, next_fn)

        chain = _build_chain(0)
        chain(topic, key, value)

class ConsumerMiddlewarePipeline:
    def __init__(self, middlewares: List[ConsumerMiddleware]) -> None:
        self.middlewares = middlewares

    def execute(self, message: Any, target_handler_fn: Callable) -> Any:
        def _build_chain(index: int):
            if index >= len(self.middlewares):
                return lambda msg: target_handler_fn(msg)
            mw = self.middlewares[index]
            next_fn = _build_chain(index + 1)
            return lambda msg: mw(msg, next_fn)

        chain = _build_chain(0)
        return chain(message)
