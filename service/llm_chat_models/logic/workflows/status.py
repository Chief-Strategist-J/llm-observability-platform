from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime

class WorkflowStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    WAITING_FOR_EVENT = 'waiting_for_event'
    WAITING_FOR_APPROVAL = 'waiting_for_approval'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

@dataclass
class WorkflowResult:
    workflow_id: str
    status: WorkflowStatus
    output: Any = None
    error: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED)

    def to_dict(self) -> Dict[str, Any]:
        return {'workflow_id': self.workflow_id, 'status': self.status.value, 'output': self.output, 'error': self.error, 'steps_completed': self.steps_completed, 'steps_total': self.steps_total, 'started_at': self.started_at.isoformat() if self.started_at else None, 'completed_at': self.completed_at.isoformat() if self.completed_at else None, 'metadata': self.metadata}