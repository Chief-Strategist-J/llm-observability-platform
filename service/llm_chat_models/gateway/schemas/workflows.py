from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class WorkflowRunRequest(BaseModel):
    name: str
    metadata: Dict[str, Any] = {}

class WorkflowActionRequest(BaseModel):
    payload: Optional[Any] = None
    reason: str = ''

class WorkflowEventRequest(BaseModel):
    event_name: str
    payload: Optional[Any] = None

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = {}

class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int