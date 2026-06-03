from typing import Any, Dict
from opentelemetry import metrics
from src.features.metrics.registry import SAFETY_METRICS_REGISTRY, MetricType


class PrometheusMetricsAdapter:
    def __init__(self, meter_name: str = "llm-observability"):
        meter = metrics.get_meter(meter_name)

        self._token_counter = meter.create_counter(
            "llm_tokens_total",
            unit="tokens",
            description="Total LLM tokens consumed",
        )

        self._cost_counter = meter.create_counter(
            "llm_cost_usd_micro_total",
            unit="usd_micro",
            description="Total LLM cost in micro-USD",
        )

        self._latency_histogram = meter.create_histogram(
            "llm_latency_ms_total",
            unit="",
            description="LLM call total latency",
        )

        self._ttft_histogram = meter.create_histogram(
            "llm_latency_ms_ttft",
            unit="",
            description="LLM time to first token",
        )

        self._pii_counter = meter.create_counter(
            "llm_pii_detected_total",
            unit="1",
            description="Total PII detections",
        )

        self._injection_counter = meter.create_counter(
            "llm_injection_attempts_total",
            unit="1",
            description="Total prompt injection attempts",
        )

        self._finish_reason_counter = meter.create_counter(
            "llm_finish_reason_total",
            unit="1",
            description="Finish reason distribution",
        )

        self._span_counter = meter.create_counter(
            "llm_spans_total",
            unit="1",
            description="Total LLM spans recorded",
        )

        self._registry_metrics: Dict[str, Any] = {}
        for evaluator in SAFETY_METRICS_REGISTRY:
            m = evaluator.metric
            if m.metric_type == MetricType.COUNTER:
                self._registry_metrics[m.name] = meter.create_counter(
                    m.name, unit=m.unit, description=m.description
                )
            elif m.metric_type == MetricType.HISTOGRAM:
                self._registry_metrics[m.name] = meter.create_histogram(
                    m.name, unit=m.unit, description=m.description
                )

    def record_tokens(self, amount: int, labels: Dict[str, str]) -> None:
        self._token_counter.add(amount, labels)

    def record_cost(self, amount: int, labels: Dict[str, str]) -> None:
        self._cost_counter.add(amount, labels)

    def record_latency(self, duration_ms: int, labels: Dict[str, str]) -> None:
        self._latency_histogram.record(duration_ms, labels)

    def record_ttft(self, duration_ms: int, labels: Dict[str, str]) -> None:
        self._ttft_histogram.record(duration_ms, labels)

    def record_pii(self, labels: Dict[str, str]) -> None:
        self._pii_counter.add(1, labels)

    def record_injection(self, labels: Dict[str, str]) -> None:
        self._injection_counter.add(1, labels)

    def record_finish_reason(self, labels: Dict[str, str]) -> None:
        self._finish_reason_counter.add(1, labels)

    def record_span(self, labels: Dict[str, str]) -> None:
        self._span_counter.add(1, labels)

    def record_metric(self, name: str, value: Any, labels: Dict[str, str]) -> None:
        instrument = self._registry_metrics.get(name)
        if instrument is None:
            return
        if hasattr(instrument, "add"):
            instrument.add(value, labels)
        elif hasattr(instrument, "record"):
            instrument.record(value, labels)
