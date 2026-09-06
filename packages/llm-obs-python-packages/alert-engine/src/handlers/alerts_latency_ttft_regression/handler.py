import logging
from typing import Any
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.metrics_port import MetricsPort
from features.latency_ttft_regression.index import LatencyTtftRegressionService, LatencyTtftRegressionAlertPayload

logger = logging.getLogger(__name__)

class LatencyTtftRegressionAlertHandler:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        slack_port: SlackPort,
        metrics_port: MetricsPort
    ) -> None:
        self.service = LatencyTtftRegressionService(
            db_port=db_port,
            redis_port=redis_port,
            slack_port=slack_port,
            metrics_port=metrics_port
        )

    def handle(self, payload: dict[str, Any]) -> None:
        model = payload.get("model") or "unknown"
        current = payload.get("current", 0.0)
        baseline = payload.get("baseline", 0.0)
        hour_of_day = payload.get("hour_of_day", 0)
        timestamp = payload.get("timestamp")

        feature_payload = LatencyTtftRegressionAlertPayload(
            model=model,
            current=current,
            baseline=baseline,
            hour_of_day=hour_of_day,
            timestamp=timestamp
        )

        self.service.process_alert(feature_payload)
