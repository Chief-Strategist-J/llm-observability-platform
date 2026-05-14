from typing import Optional, Any, Dict
from .reporter import SpanReporter

class NoOpReporter:
    def report(self, span_data: Dict[str, Any]) -> None:
        pass

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        pass

_REPORTER: SpanReporter = NoOpReporter()

def set_reporter(reporter: SpanReporter) -> None:
    global _REPORTER
    _REPORTER = reporter

def get_reporter() -> SpanReporter:
    return _REPORTER
