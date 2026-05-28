import json
import urllib.request
import urllib.error
from opentelemetry import trace
from shared.ports.slack_port import SlackPort

tracer = trace.get_tracer("alert-engine")

class SlackAdapter(SlackPort):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _post(self, payload: dict) -> None:
        with tracer.start_as_current_span(
            "slack_adapter.post",
            attributes={
                "http.url": self.webhook_url,
                "slack.channel": payload.get("channel", ""),
            }
        ) as span:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
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

    def send_channel_message(self, channel: str, text: str) -> None:
        self._post({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        self._post({"channel": user, "text": text})

