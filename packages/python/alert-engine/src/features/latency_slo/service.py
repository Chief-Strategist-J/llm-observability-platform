import logging
from datetime import datetime, timezone
from typing import Any
from opentelemetry import trace
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.pagerduty_port import PagerDutyPort
from shared.ports.metrics_port import MetricsPort
from features.latency_slo.types import LatencySloAlertPayload

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("alert-engine")

class LatencySloService:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        slack_port: SlackPort,
        pagerduty_port: PagerDutyPort,
        metrics_port: MetricsPort
    ) -> None:
        self.db_port = db_port
        self.redis_port = redis_port
        self.slack_port = slack_port
        self.pagerduty_port = pagerduty_port
        self.metrics_port = metrics_port

    def process_alert(self, payload: LatencySloAlertPayload) -> None:
        model = payload.model
        endpoint = payload.endpoint
        severity = payload.severity
        burn_rate = payload.burn_rate
        p95_current = payload.p95_current
        p95_baseline = payload.p95_baseline
        p99_current = payload.p99_current
        p99_baseline = payload.p99_baseline
        budget_remaining = payload.budget_remaining
        timestamp = payload.timestamp

        with tracer.start_as_current_span(
            "latency_slo_service.process_alert",
            attributes={
                "alert.type": "latency_slo",
                "model": model,
                "endpoint": endpoint,
                "severity": severity,
                "burn_rate": burn_rate,
                "budget_remaining": budget_remaining,
            }
        ) as span:
            now = datetime.now(timezone.utc)
            delivery_latency_ms = None
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    delivery_latency_ms = max(0, int((now - dt).total_seconds() * 1000))
                except Exception:
                    pass

            if severity == "page":
                # Suppress page if same (model, endpoint) paged in last 15 min (900 seconds)
                rate_limit_key = f"rate_limit:latency_slo_page:{model}:{endpoint}"
                with tracer.start_as_current_span("latency_slo_service.check_rate_limit") as sub_span:
                    sub_span.set_attribute("rate_limit.key", rate_limit_key)
                    acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 900)
                    sub_span.set_attribute("rate_limit.acquired", acquired)
                    if not acquired:
                        span.set_attribute("alert.suppressed", True)
                        logger.info("Latency SLO page alert suppressed for model=%s endpoint=%s due to rate limit", model, endpoint)
                        return

                title = f"Latency SLO breach: {model}/{endpoint}"
                custom_details = {
                    "model": model,
                    "endpoint": endpoint,
                    "burn_rate": burn_rate,
                    "p95_current": p95_current,
                    "p95_baseline": p95_baseline,
                    "p99_current": p99_current,
                    "p99_baseline": p99_baseline,
                    "budget_remaining": budget_remaining
                }
                
                with tracer.start_as_current_span("latency_slo_service.notify_pagerduty"):
                    self.pagerduty_port.trigger_incident(
                        summary=title,
                        severity="critical",
                        source="alert-engine",
                        custom_details=custom_details
                    )
                logger.info("PagerDuty alert triggered: %s", title)

            elif severity == "slack":
                slack_msg = (
                    f"🚨 *Latency SLO Breach* 🚨\n"
                    f"*Model:* `{model}`\n"
                    f"*Endpoint:* `{endpoint}`\n"
                    f"*Burn Rate:* `{burn_rate:.2f}`\n"
                    f"*P95 Current vs Baseline:* `{p95_current:.2f}ms` / `{p95_baseline:.2f}ms`\n"
                    f"*P99 Current vs Baseline:* `{p99_current:.2f}ms` / `{p99_baseline:.2f}ms`\n"
                    f"*Budget Remaining:* `{budget_remaining:.2f}%`"
                )
                with tracer.start_as_current_span("latency_slo_service.notify_slack"):
                    self.slack_port.send_channel_message("#llm-latency-alerts", slack_msg)
                logger.info("Slack alert sent to #llm-latency-alerts for %s/%s", model, endpoint)

            elif severity == "ticket":
                # Create task in Reliability project (or log to alert_history only)
                with tracer.start_as_current_span("latency_slo_service.insert_database"):
                    # Convert payload to dictionary for database insertion
                    db_payload = {
                        "model": model,
                        "endpoint": endpoint,
                        "severity": severity,
                        "burn_rate": burn_rate,
                        "p95_current": p95_current,
                        "p95_baseline": p95_baseline,
                        "p99_current": p99_current,
                        "p99_baseline": p99_baseline,
                        "budget_remaining": budget_remaining,
                        "timestamp": timestamp
                    }
                    self.db_port.insert_alert(
                        alert_type="latency_slo",
                        service=endpoint,
                        model=model,
                        user_id=None,
                        event_type="ticket",
                        payload=db_payload,
                        delivery_latency_ms=delivery_latency_ms
                    )
                logger.info("Latency SLO ticket alert logged to alert_history for model=%s endpoint=%s", model, endpoint)

            # Record delivery latency metrics if metric port is available
            if delivery_latency_ms is not None:
                try:
                    self.metrics_port.record_delivery_latency(
                        alert_type="latency_slo",
                        severity=severity,
                        latency_ms=float(delivery_latency_ms)
                    )
                except Exception:
                    pass
