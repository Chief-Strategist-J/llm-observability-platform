import logging
from datetime import datetime, timezone
from opentelemetry import trace
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.metrics_port import MetricsPort
from features.latency_ttft_regression.types import LatencyTtftRegressionAlertPayload

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("alert-engine")

class LatencyTtftRegressionService:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        slack_port: SlackPort,
        metrics_port: MetricsPort
    ) -> None:
        self.db_port = db_port
        self.redis_port = redis_port
        self.slack_port = slack_port
        self.metrics_port = metrics_port

    def process_alert(self, payload: LatencyTtftRegressionAlertPayload) -> None:
        model = payload.model
        current = payload.current
        baseline = payload.baseline
        hour_of_day = payload.hour_of_day
        timestamp = payload.timestamp

        with tracer.start_as_current_span(
            "latency_ttft_regression_service.process_alert",
            attributes={
                "alert.type": "latency_ttft_regression",
                "model": model,
                "current": current,
                "baseline": baseline,
                "hour_of_day": hour_of_day,
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

            rate_limit_key = f"rate_limit:latency_ttft_regression:{model}:{hour_of_day}"
            with tracer.start_as_current_span("latency_ttft_regression_service.check_rate_limit") as sub_span:
                sub_span.set_attribute("rate_limit.key", rate_limit_key)
                acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 21600)  # 6 hours
                sub_span.set_attribute("rate_limit.acquired", acquired)
                if not acquired:
                    span.set_attribute("alert.suppressed", True)
                    logger.info("Latency TTFT regression alert suppressed for model=%s hour_of_day=%s due to rate limit", model, hour_of_day)
                    return

            # Insert into database
            with tracer.start_as_current_span("latency_ttft_regression_service.insert_database"):
                db_payload = {
                    "model": model,
                    "current": current,
                    "baseline": baseline,
                    "hour_of_day": hour_of_day,
                    "timestamp": timestamp
                }
                self.db_port.insert_alert(
                    alert_type="latency_ttft_regression",
                    service=None,
                    model=model,
                    user_id=None,
                    event_type="slack",
                    payload=db_payload,
                    delivery_latency_ms=delivery_latency_ms
                )

            # Send slack notification
            slack_msg = f"{model} TTFT P99 degraded: {current}ms vs {baseline}ms baseline at {hour_of_day}:00 UTC. Possible provider degradation."
            with tracer.start_as_current_span("latency_ttft_regression_service.notify_slack"):
                self.slack_port.send_channel_message("#llm-latency-alerts", slack_msg)
            logger.info("Slack alert sent to #llm-latency-alerts for TTFT regression on %s", model)

            # Record metrics
            if delivery_latency_ms is not None:
                try:
                    self.metrics_port.record_delivery_latency(
                        alert_type="latency_ttft_regression",
                        severity="slack",
                        latency_ms=float(delivery_latency_ms)
                    )
                except Exception:
                    pass
