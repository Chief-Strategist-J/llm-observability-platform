from typing import Protocol, runtime_checkable
from typing import Any, Dict

@runtime_checkable
class SpanReporter(Protocol):
    def report(self, span_data: Dict[str, Any]) -> None:
        ...

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        ...
