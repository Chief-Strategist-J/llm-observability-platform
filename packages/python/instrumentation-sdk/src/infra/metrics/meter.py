import os
from typing import Optional
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server


_meter_initialized = False


def init_meter(port: Optional[int] = None) -> None:
    global _meter_initialized
    if _meter_initialized:
        return

    reader = PrometheusMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)

    listen_port = port or int(os.getenv("PROMETHEUS_METRICS_PORT", "9464"))
    try:
        start_http_server(listen_port)
    except OSError:
        pass

    _meter_initialized = True
