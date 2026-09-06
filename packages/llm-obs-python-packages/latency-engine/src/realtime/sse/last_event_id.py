import os

class LastEventIdStore:
    def __init__(self, filepath: str = "/tmp/sse_last_event_id.txt") -> None:
        self.filepath = filepath

    def get(self) -> str | None:
        """Read the stored Last-Event-ID."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return f.read().strip() or None
            except Exception:
                return None
        return None

    def save(self, event_id: str) -> None:
        """Store the Last-Event-ID."""
        try:
            with open(self.filepath, "w") as f:
                f.write(event_id)
        except Exception:
            pass

    def inject_header(self, headers: dict[str, str]) -> dict[str, str]:
        """Inject Last-Event-ID into reconnect headers if present."""
        last_id = self.get()
        if last_id:
            headers["Last-Event-ID"] = last_id
        return headers
