from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SessionContext:
    session_id: str
    agent_type: str
    provider: str
    collection: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
