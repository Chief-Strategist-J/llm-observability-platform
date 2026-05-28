import json
import urllib.request
import urllib.error
from shared.ports.slack_port import SlackPort

class SlackAdapter(SlackPort):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _post(self, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                resp.read()
        except urllib.error.URLError:
            pass

    def send_channel_message(self, channel: str, text: str) -> None:
        self._post({"channel": channel, "text": text})

    def send_direct_message(self, user: str, text: str) -> None:
        self._post({"channel": user, "text": text})
