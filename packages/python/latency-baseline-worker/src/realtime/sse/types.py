from dataclasses import dataclass, asdict
import json

@dataclass
class SSEEvent:
    event_type: str
    data: dict
    workflow_id: str
    run_id: str
    attempt: int
    id: str | None = None

    def serialize(self) -> str:
        payload = {
            "event_type": self.event_type,
            "data": self.data,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "attempt": self.attempt,
        }
        return json.dumps(payload)
