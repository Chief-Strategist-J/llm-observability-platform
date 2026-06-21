from typing import Any, Dict, Optional
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

        # Observable (callback-based) gauges so that the last value is
        # continuously reported on every Prometheus scrape, not just once.
        self._forecast_mean_value: Optional[float] = None
        self._forecast_mean_labels: Dict[str, str] = {}

        self._forecast_p10_value: Optional[float] = None
        self._forecast_p10_labels: Dict[str, str] = {}

        self._forecast_p90_value: Optional[float] = None
        self._forecast_p90_labels: Dict[str, str] = {}

        self._forecast_cost_mean = meter.create_observable_gauge(
            "llm_forecast_cost_mean",
            callbacks=[self._observe_forecast_mean],
            unit="usd_micro",
            description="Forecasted mean cost in micro-USD",
        )

        self._forecast_cost_p10 = meter.create_observable_gauge(
            "llm_forecast_cost_p10",
            callbacks=[self._observe_forecast_p10],
            unit="usd_micro",
            description="Forecasted p10 cost in micro-USD",
        )

        self._forecast_cost_p90 = meter.create_observable_gauge(
            "llm_forecast_cost_p90",
            callbacks=[self._observe_forecast_p90],
            unit="usd_micro",
            description="Forecasted p90 cost in micro-USD",
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

    # ---------------------------------------------------------------------------
    # Observable gauge callbacks – called by the OTel SDK on every collection
    # ---------------------------------------------------------------------------

    def _observe_forecast_mean(self, options):
        if self._forecast_mean_value is not None:
            yield metrics.Observation(self._forecast_mean_value, self._forecast_mean_labels)

    def _observe_forecast_p10(self, options):
        if self._forecast_p10_value is not None:
            yield metrics.Observation(self._forecast_p10_value, self._forecast_p10_labels)

    def _observe_forecast_p90(self, options):
        if self._forecast_p90_value is not None:
            yield metrics.Observation(self._forecast_p90_value, self._forecast_p90_labels)

    # ---------------------------------------------------------------------------
    # Public recording methods
    # ---------------------------------------------------------------------------

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

    def record_forecast_mean(self, amount: int, labels: Dict[str, str]) -> None:
        self._forecast_mean_value = float(amount)
        self._forecast_mean_labels = labels

    def record_forecast_p10(self, amount: int, labels: Dict[str, str]) -> None:
        self._forecast_p10_value = float(amount)
        self._forecast_p10_labels = labels

    def record_forecast_p90(self, amount: int, labels: Dict[str, str]) -> None:
        self._forecast_p90_value = float(amount)
        self._forecast_p90_labels = labels

    def record_metric(self, name: str, value: Any, labels: Dict[str, str]) -> None:
        instrument = self._registry_metrics.get(name)
        if instrument is None:
            return
        if hasattr(instrument, "add"):
            instrument.add(value, labels)
        elif hasattr(instrument, "record"):
            instrument.record(value, labels)
