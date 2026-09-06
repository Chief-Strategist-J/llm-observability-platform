from datetime import datetime, timezone
from typing import Any
from opentelemetry import trace
from shared.ports.db_port import DbPort
from shared.ports.redis_port import RedisPort
from shared.ports.slack_port import SlackPort
from shared.ports.pagerduty_port import PagerDutyPort
from shared.ports.metrics_port import MetricsPort

tracer = trace.get_tracer("alert-engine")

class CostAnomalyAlertHandler:
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

    def handle(self, payload: dict[str, Any]) -> None:
        service = payload.get("service")
        model = payload.get("model")
        sample_count = payload.get("sample_count", 0)
        current_cost = payload.get("current_cost", 0.0)
        ewma_value = payload.get("ewma_value", 0.0)
        timestamp = payload.get("timestamp")

        with tracer.start_as_current_span(
            "cost_anomaly_alert_handler.handle",
            attributes={
                "alert.type": "cost_anomaly",
                "service": service or "unknown",
                "model": model or "unknown",
                "sample_count": sample_count,
                "current_cost": current_cost,
                "ewma_value": ewma_value,
            }
        ) as span:
            if not service or not model:
                span.set_status(trace.StatusCode.ERROR, "Missing required fields")
                return

            is_cold_start = payload.get("is_cold_start")
            if is_cold_start is None:
                is_cold_start = (sample_count < 7)

            now = datetime.now(timezone.utc)
            delivery_latency_ms = None
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    delivery_latency_ms = max(0, int((now - dt).total_seconds() * 1000))
                except Exception:
                    pass

            if is_cold_start:
                span.set_attribute("alert.cold_start", True)
                with tracer.start_as_current_span("cost_anomaly_alert_handler.insert_database"):
                    self.db_port.insert_alert(
                        alert_type="cost_anomaly",
                        service=service,
                        model=model,
                        user_id=None,
                        event_type="cold_start",
                        payload=payload,
                        delivery_latency_ms=delivery_latency_ms
                    )
                if delivery_latency_ms is not None:
                    self.metrics_port.record_delivery_latency(
                        alert_type="cost_anomaly",
                        severity="info",
                        latency_ms=float(delivery_latency_ms)
                    )
                return

            burn_ratio = (current_cost / ewma_value) if ewma_value > 0 else 0.0
            span.set_attribute("alert.burn_ratio", burn_ratio)
            if burn_ratio > 3.0:
                rate_limit_key = f"rate_limit:cost_anomaly:{service}:{model}"
                with tracer.start_as_current_span("cost_anomaly_alert_handler.check_rate_limit") as sub_span:
                    sub_span.set_attribute("rate_limit.key", rate_limit_key)
                    acquired = self.redis_port.acquire_rate_limit(rate_limit_key, 3600)
                    sub_span.set_attribute("rate_limit.acquired", acquired)
                    if not acquired:
                        span.set_attribute("alert.suppressed", True)
                        return

                with tracer.start_as_current_span("cost_anomaly_alert_handler.insert_database"):
                    self.db_port.insert_alert(
                        alert_type="cost_anomaly",
                        service=service,
                        model=model,
                        user_id=None,
                        event_type="spike",
                        payload=payload,
                        delivery_latency_ms=delivery_latency_ms
                    )

                if delivery_latency_ms is not None:
                    self.metrics_port.record_delivery_latency(
                        alert_type="cost_anomaly",
                        severity="critical",
                        latency_ms=float(delivery_latency_ms)
                    )

                cluster_drilldown = payload.get("cluster_drilldown", [])
                top_cluster_name = "unknown"
                top_cluster_cost = 0.0
                if cluster_drilldown:
                    try:
                        top_cluster = max(cluster_drilldown, key=lambda c: c.get("cost", 0.0))
                        top_cluster_name = top_cluster.get("cluster_id", "unknown")
                        top_cluster_cost = top_cluster.get("cost", 0.0)
                    except Exception:
                        pass

                slack_msg = (
                    f"Cost spike: {service}/{model} — ${current_cost:.4f} vs "
                    f"${ewma_value:.4f} baseline. Likely cause: prompt cluster "
                    f"'{top_cluster_name}' (${top_cluster_cost:.4f} of spike)"
                )
                with tracer.start_as_current_span("cost_anomaly_alert_handler.notify_slack"):
                    self.slack_port.send_channel_message("#llm-cost-alerts", slack_msg)

                with tracer.start_as_current_span("cost_anomaly_alert_handler.notify_pagerduty"):
                    self.pagerduty_port.trigger_incident(
                        summary=f"Cost spike: {service}/{model} - burn ratio {burn_ratio:.2f}",
                        severity="critical",
                        source="alert-engine",
                        custom_details={
                            "service": service,
                            "model": model,
                            "current_cost": current_cost,
                            "baseline_cost": ewma_value,
                            "burn_ratio": burn_ratio,
                            "top_cluster": top_cluster_name,
                            "top_cluster_cost": top_cluster_cost
                        }
                    )
            else:
                span.set_attribute("alert.suppressed", True)
                span.set_attribute("alert.suppression_reason", "burn_ratio_under_threshold")

