from typing import Dict, Any, Optional
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.propagation import inject, extract

class MessagingContextPropagation:
    @staticmethod
    def inject_context(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        if headers is None:
            headers = {}
        inject(headers)
        return headers

    @staticmethod
    def extract_context(headers: Dict[str, str]):
        return extract(headers)
