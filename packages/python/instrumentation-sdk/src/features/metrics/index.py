from typing import Any, Dict, Optional
from .infra.adapters.prometheus_adapter import PrometheusMetricsAdapter
from .service import MetricsService


class _NoOpAdapter:
    def record_tokens(self, amount, labels):
        pass

    def record_cost(self, amount, labels):
        pass

    def record_latency(self, duration_ms, labels):
        pass

    def record_ttft(self, duration_ms, labels):
        pass

    def record_pii(self, labels):
        pass

    def record_injection(self, labels):
        pass

    def record_finish_reason(self, labels):
        pass

    def record_span(self, labels):
        pass


_adapter = _NoOpAdapter()
_service = MetricsService(_adapter)
_initialized = False


def init_metrics_pipeline(port: Optional[int] = None) -> None:
    global _adapter, _service, _initialized
    if _initialized:
        return
    from ...infra.metrics.meter import init_meter
    init_meter(port)
    _adapter = PrometheusMetricsAdapter()
    _service = MetricsService(_adapter)
    _initialized = True


def record_span_metrics(span_data: Dict[str, Any]) -> None:
    _service.record_span_telemetry(span_data)
