from typing import Any, Dict, Optional, List
from .infra.adapters.prometheus_adapter import PrometheusMetricsAdapter
from .service import MetricsService
from src.infra.adapters.price_watcher import PriceWatcherAdapter


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


_price_watcher = PriceWatcherAdapter()
_adapter = _NoOpAdapter()
_service = MetricsService(_adapter, price_config=_price_watcher)
_initialized = False


def init_metrics_pipeline(port: Optional[int] = None) -> None:
    global _adapter, _service, _initialized
    if _initialized:
        return
    from src.infra.metrics.meter import init_meter
    init_meter(port)
    _adapter = PrometheusMetricsAdapter()
    _service = MetricsService(_adapter, price_config=_price_watcher)
    _initialized = True


def record_span_metrics(span_data: Dict[str, Any]) -> None:
    _service.record_span_telemetry(span_data)


def get_current_prices_ref() -> List[Dict[str, Any]]:
    return _price_watcher.get_prices()


def reload_prices() -> None:
    _price_watcher.reload()

