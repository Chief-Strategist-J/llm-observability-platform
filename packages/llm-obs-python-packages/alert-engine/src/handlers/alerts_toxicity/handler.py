import logging
from typing import Any
from opentelemetry import trace
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("alert-engine")

class ToxicityAlertHandler:
    def __init__(
        self,
        redis_port: RedisPort,
        slack_port: SlackPort,
    ) -> None:
        self.redis_port = redis_port
        self.slack_port = slack_port

    def handle(self, payload: dict[str, Any]) -> None:
        span_id = payload.get("span_id")
        user_id = payload.get("user_id") or "unknown"
        endpoint = payload.get("endpoint") or "unknown"
        toxicity_score = payload.get("toxicity_score")
        model = payload.get("model") or "unknown"

        with tracer.start_as_current_span(
            "toxicity_alert_handler.handle",
            attributes={
                "alert.type": "toxicity",
                "span_id": span_id or "unknown",
                "user_id": user_id,
                "endpoint": endpoint,
            }
        ) as span:
            if not span_id or toxicity_score is None:
                span.set_status(trace.StatusCode.ERROR, "Missing required fields")
                return

            # Dedup: same user_id + same endpoint within 5 min (300 seconds) -> 1 alert only
            rate_limit_key = f"rate_limit:toxicity_alert:{user_id}:{endpoint}"
            with tracer.start_as_current_span("toxicity_alert_handler.check_rate_limit") as sub_span:
                sub_span.set_attribute("rate_limit.key", rate_limit_key)
                # 5 minutes is 300 seconds
                acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 300)
                sub_span.set_attribute("rate_limit.acquired", acquired)
                if not acquired:
                    span.set_attribute("alert.suppressed", True)
                    return

            msg = (
                f"Toxicity alert: high toxicity detected in response. "
                f"Span ID: {span_id}, User ID: {user_id}, Endpoint: {endpoint}, "
                f"Model: {model}, Toxicity Score: {toxicity_score:.4f}"
            )
            with tracer.start_as_current_span("toxicity_alert_handler.notify_slack"):
                self.slack_port.send_channel_message("#llm-safety-review", msg)
