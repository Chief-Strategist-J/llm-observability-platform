from __future__ import annotations

from infra.messaging.reporters.span_reporter import SpanReporter


class AnomalyPublisherEntry:
    def __init__(self) -> None:
        self.reporter = SpanReporter()

    def publish_anomaly(self, model: str, metric_name: str, current_value: float, threshold_value: float) -> None:
        self.reporter.report_anomaly(model, metric_name, current_value, threshold_value)
