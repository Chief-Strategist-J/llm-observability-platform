import logging
import urllib.request
import urllib.parse
import json
from typing import Callable, Any
from realtime.sse.types import SSEEvent
from realtime.sse.last_event_id import LastEventIdStore
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class SSEClient:
    def __init__(self, last_event_id_store: LastEventIdStore | None = None) -> None:
        self.store = last_event_id_store or LastEventIdStore()
        self.connected = False
        self._conn = None

    def connect(self, url: str) -> bool:
        """Connect to SSE endpoint, sending the Last-Event-ID in headers."""
        try:
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
            }
            headers = self.store.inject_header(headers)
            
            req = urllib.request.Request(url, headers=headers)
            self._conn = urllib.request.urlopen(req, timeout=5)
            self.connected = True
            logger.info("Successfully connected to SSE endpoint: %s", url)
            return True
        except Exception as e:
            logger.error("Failed to connect to SSE endpoint: %s", e)
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect the client."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self.connected = False
        logger.info("Disconnected from SSE endpoint.")

    def send_event(self, url: str, event: SSEEvent) -> bool:
        """Push an event to the server via POST (carrying workflow_id, run_id, attempt)."""
        with trace_span("realtime.sse.send_event") as span:
            span.set_attribute("workflow_id", event.workflow_id)
            span.set_attribute("run_id", event.run_id)
            span.set_attribute("attempt", event.attempt)

            try:
                data = event.serialize().encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = response.read().decode("utf-8")
                    # If response contains a new event ID, store it
                    try:
                        res_json = json.loads(res_data)
                        if "id" in res_json:
                            self.store.save(res_json["id"])
                    except Exception:
                        pass
                return True
            except Exception as e:
                logger.error("Failed to send event to %s: %s", url, e)
                return False
