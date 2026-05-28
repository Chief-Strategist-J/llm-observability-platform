import yaml
from datetime import datetime, timezone
from typing import Any
from opentelemetry import trace
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.metrics_port import MetricsPort

tracer = trace.get_tracer("alert-engine")

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
        with tracer.start_as_current_span("budget_alert_handler.load_owners"):
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

        with tracer.start_as_current_span(
            "budget_alert_handler.handle",
            attributes={
                "alert.type": "budget",
                "user_id": user_id or "unknown",
                "model": model or "unknown",
                "event_type": event_type or "unknown",
            }
        ) as span:
            if not user_id or not model or not event_type:
                span.set_status(trace.StatusCode.ERROR, "Missing required fields")
                return

            rate_limit_key = f"rate_limit:budget_alert:{user_id}:{model}"
            with tracer.start_as_current_span("budget_alert_handler.check_rate_limit") as sub_span:
                sub_span.set_attribute("rate_limit.key", rate_limit_key)
                acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 900)
                sub_span.set_attribute("rate_limit.acquired", acquired)
                if not acquired:
                    span.set_attribute("alert.suppressed", True)
                    return

            now = datetime.now(timezone.utc)
            delivery_latency_ms = None
            if timestamp_utc:
                try:
                    dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
                    delivery_latency_ms = max(0, int((now - dt).total_seconds() * 1000))
                except Exception:
                    pass

            with tracer.start_as_current_span("budget_alert_handler.insert_database"):
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
                with tracer.start_as_current_span("budget_alert_handler.notify_slack_channel"):
                    self.slack_port.send_channel_message("#llm-cost-alerts", msg)
            elif event_type == "warning_80pct":
                service = payload.get("service") or "default"
                owners = self._load_owners()
                owner = owners.get(service)
                if owner:
                    msg = f"Budget warning: user '{user_id}' has consumed 80% of budget for model '{model}'."
                    with tracer.start_as_current_span(
                        "budget_alert_handler.notify_slack_owner",
                        attributes={"owner": owner}
                    ):
                        self.slack_port.send_direct_message(owner, msg)
                else:
                    span.set_attribute("owner.missing", True)

