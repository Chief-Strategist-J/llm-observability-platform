import yaml
from datetime import datetime, timezone
from typing import Any
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.metrics_port import MetricsPort

class BudgetAlertHandler:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        slack_port: SlackPort,
        metrics_port: MetricsPort,
        service_owners_path: str
    ) -> None:
        self.db_port = db_port
        self.redis_port = redis_port
        self.slack_port = slack_port
        self.metrics_port = metrics_port
        self.service_owners_path = service_owners_path

    def _load_owners(self) -> dict[str, str]:
        try:
            with open(self.service_owners_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("service_owners", {})
        except Exception:
            return {}

    def handle(self, payload: dict[str, Any]) -> None:
        user_id = payload.get("user_id")
        model = payload.get("model")
        event_type = payload.get("event_type")
        timestamp_utc = payload.get("timestamp_utc")

        if not user_id or not model or not event_type:
            return

        rate_limit_key = f"rate_limit:budget_alert:{user_id}:{model}"
        if not self.redis_port.acquire_rate_limit(rate_limit_key, 900):
            return

        now = datetime.now(timezone.utc)
        delivery_latency_ms = None
        if timestamp_utc:
            try:
                dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
                delivery_latency_ms = max(0, int((now - dt).total_seconds() * 1000))
            except Exception:
                pass

        self.db_port.insert_alert(
            alert_type="budget",
            service=payload.get("service"),
            model=model,
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            delivery_latency_ms=delivery_latency_ms
        )

        severity = "critical" if event_type == "blocked" else "warning"
        if delivery_latency_ms is not None:
            self.metrics_port.record_delivery_latency(
                alert_type="budget",
                severity=severity,
                latency_ms=float(delivery_latency_ms)
            )

        if event_type == "blocked":
            msg = f"Budget exceeded: user '{user_id}' blocked for model '{model}'."
            self.slack_port.send_channel_message("#llm-cost-alerts", msg)
        elif event_type == "warning_80pct":
            service = payload.get("service") or "default"
            owners = self._load_owners()
            owner = owners.get(service)
            if owner:
                msg = f"Budget warning: user '{user_id}' has consumed 80% of budget for model '{model}'."
                self.slack_port.send_direct_message(owner, msg)
