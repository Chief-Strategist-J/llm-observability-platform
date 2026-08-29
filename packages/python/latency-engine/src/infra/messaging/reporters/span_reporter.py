from __future__ import annotations

import logging
from typing import Any
from infra.messaging.producer.factory.producer_factory import ProducerFactory

logger = logging.getLogger(__name__)


class SpanReporter:
    def __init__(self, topic: str = "latency.anomalies.v1") -> None:
        self.topic = topic
        self.client = ProducerFactory.create_client(client_id_suffix="reporter")

    def report_anomaly(self, model: str, metric_name: str, current_val: float, threshold_val: float) -> None:
        payload = {
            "model": model,
            "metric_name": metric_name,
            "current_value_ms": current_val,
            "threshold_ms": threshold_val,
        }
        self.client.produce(self.topic, payload, key=model)
