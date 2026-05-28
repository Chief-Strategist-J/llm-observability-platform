import json
import urllib.request
import urllib.error
from typing import Any
from opentelemetry import trace
from shared.ports.pagerduty_port import PagerDutyPort

tracer = trace.get_tracer("alert-engine")

class PagerDutyAdapter(PagerDutyPort):
    def __init__(self, routing_key: str, endpoint: str = "https://events.pagerduty.com/v2/enqueue"):
        self.routing_key = routing_key
        self.endpoint = endpoint

    def trigger_incident(
        self,
        summary: str,
        severity: str,
        source: str,
        custom_details: dict[str, Any] | None = None
    ) -> None:
        with tracer.start_as_current_span(
            "pagerduty_adapter.trigger_incident",
            attributes={
                "http.url": self.endpoint,
                "pagerduty.summary": summary,
                "pagerduty.severity": severity,
                "pagerduty.source": source,
            }
        ) as span:
            payload = {
                "routing_key": self.routing_key,
                "event_action": "trigger",
                "payload": {
                    "summary": summary,
                    "severity": severity,
                    "source": source,
                    "custom_details": custom_details or {}
                }
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    resp.read()
            except urllib.error.URLError as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                pass

