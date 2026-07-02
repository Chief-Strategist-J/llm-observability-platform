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
    ) -> str | None:
        with tracer.start_as_current_span(
            "pagerduty_adapter.trigger_incident",
            attributes={
                "http.url": self.endpoint,
                "pagerduty.summary": summary,
                "pagerduty.severity": severity,
                "pagerduty.source": source,
            }
        ) as span:
            # We can use a generated dedup_key or return the one from PD API response.
            # PD Events API v2 accepts custom dedup_key. If not provided, PD creates one and returns it.
            # To be robust, let's generate a unique dedup_key based on model & endpoint if passed in custom_details
            dedup_key = None
            if custom_details:
                model = custom_details.get("model")
                endpoint = custom_details.get("endpoint")
                if model and endpoint:
                    dedup_key = f"latency_slo:{model}:{endpoint}".replace("/", "_")

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
            if dedup_key:
                payload["dedup_key"] = dedup_key

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    returned_dedup = resp_data.get("dedup_key")
                    return returned_dedup or dedup_key
            except urllib.error.URLError as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                return dedup_key

    def resolve_incident(
        self,
        dedup_key: str
    ) -> None:
        with tracer.start_as_current_span(
            "pagerduty_adapter.resolve_incident",
            attributes={
                "http.url": self.endpoint,
                "pagerduty.dedup_key": dedup_key,
            }
        ) as span:
            payload = {
                "routing_key": self.routing_key,
                "event_action": "resolve",
                "dedup_key": dedup_key
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


