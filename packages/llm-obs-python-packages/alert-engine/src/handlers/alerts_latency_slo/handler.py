import logging
from typing import Any
from opentelemetry import trace
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.pagerduty_port import PagerDutyPort
from shared.ports.metrics_port import MetricsPort
from features.latency_slo.index import LatencySloService, LatencySloAlertPayload

logger = logging.getLogger(__name__)

class LatencySloAlertHandler:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        slack_port: SlackPort,
        pagerduty_port: PagerDutyPort,
        metrics_port: MetricsPort
    ) -> None:
        self.service = LatencySloService(
            db_port=db_port,
            redis_port=redis_port,
            slack_port=slack_port,
            pagerduty_port=pagerduty_port,
            metrics_port=metrics_port
        )

    def handle(self, payload: dict[str, Any]) -> None:
        model = payload.get("model") or "unknown"
        endpoint = payload.get("endpoint") or "unknown"
        severity = payload.get("severity") or "ticket"
        burn_rate = payload.get("burn_rate", 0.0)
        p95_current = payload.get("p95_current", 0.0)
        p95_baseline = payload.get("p95_baseline", 0.0)
        p99_current = payload.get("p99_current", 0.0)
        p99_baseline = payload.get("p99_baseline", 0.0)
        budget_remaining = payload.get("budget_remaining", 0.0)
        timestamp = payload.get("timestamp")

        feature_payload = LatencySloAlertPayload(
            model=model,
            endpoint=endpoint,
            severity=severity,
            burn_rate=burn_rate,
            p95_current=p95_current,
            p95_baseline=p95_baseline,
            p99_current=p99_current,
            p99_baseline=p99_baseline,
            budget_remaining=budget_remaining,
            timestamp=timestamp
        )

        self.service.process_alert(feature_payload)
