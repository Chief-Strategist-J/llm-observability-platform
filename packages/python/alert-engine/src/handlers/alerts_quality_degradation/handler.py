import logging
from typing import Any
from opentelemetry import trace
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("alert-engine")


class QualityDegradationAlertHandler:
    """
    Handles alerts.quality.degradation events.
    Deduplicates alerts per model+endpoint with 1-hour TTL.
    Suppresses Slack notification when is_cold_start=True (logs warning only).
    """

    def __init__(
        self,
        redis_port: RedisPort,
        slack_port: SlackPort,
    ) -> None:
        self.redis_port = redis_port
        self.slack_port = slack_port

    def handle(self, payload: dict[str, Any]) -> None:
        model = payload.get("model")
        endpoint = payload.get("endpoint")
        current_window_avg = payload.get("current_window_avg")
        baseline = payload.get("baseline")
        ratio = payload.get("ratio")
        alerted_at = payload.get("alerted_at")
        is_cold_start: bool = bool(payload.get("is_cold_start", False))

        with tracer.start_as_current_span(
            "quality_degradation_alert_handler.handle",
            attributes={
                "alert.type": "quality_degradation",
                "model": model or "unknown",
                "endpoint": endpoint or "unknown",
                "is_cold_start": is_cold_start,
            },
        ) as span:
            # Validate required fields
            if (
                model is None
                or endpoint is None
                or current_window_avg is None
                or baseline is None
                or ratio is None
                or alerted_at is None
            ):
                span.set_status(trace.StatusCode.ERROR, "Missing required fields")
                logger.warning(
                    "quality_degradation_handler: missing required fields in payload=%s",
                    payload,
                )
                return

            # Cold-start suppression: log warning but skip Slack alert
            if is_cold_start:
                logger.warning(
                    "quality_degradation_handler: cold-start suppressed alert "
                    "model=%s endpoint=%s current_avg=%.4f baseline=%.4f ratio=%.4f",
                    model, endpoint, current_window_avg, baseline, ratio,
                )
                span.set_attribute("alert.cold_start_suppressed", True)
                return

            # Dedup: rate limit key per model+endpoint, TTL 3600 seconds (1 hour)
            rate_limit_key = f"rate_limit:quality_degradation:{model}:{endpoint}"
            with tracer.start_as_current_span(
                "quality_degradation_alert_handler.check_rate_limit"
            ) as sub_span:
                sub_span.set_attribute("rate_limit.key", rate_limit_key)
                acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 3600)
                sub_span.set_attribute("rate_limit.acquired", acquired)
                if not acquired:
                    span.set_attribute("alert.suppressed", True)
                    return

            msg = (
                f"Quality degradation alert: model={model} endpoint={endpoint} "
                f"current_avg={current_window_avg:.4f} baseline={baseline:.4f} "
                f"ratio={ratio:.4f} alerted_at={alerted_at}"
            )
            logger.error(
                "quality_degradation_handler: degradation detected "
                "model=%s endpoint=%s current_avg=%.4f baseline=%.4f ratio=%.4f",
                model, endpoint, current_window_avg, baseline, ratio,
            )
            with tracer.start_as_current_span(
                "quality_degradation_alert_handler.notify_slack"
            ):
                self.slack_port.send_channel_message("#llm-quality-alerts", msg)
