from fastapi import APIRouter
from pydantic import BaseModel
import os
from opentelemetry import trace
from .....features.spans.tool_call_tracker import track_tool_call, clear_tool_call_tracker, get_trace_total_cost

router = APIRouter(prefix="/tool-call", tags=["Tool Call Tracking"])

class ToolCallTrackRequest(BaseModel):
    trace_id: str
    span_id: str
    cost: int

class ToolCallTrackResponse(BaseModel):
    total_cost: int

class ToolCallClearResponse(BaseModel):
    success: bool

def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "tool_call_tracking")

@router.post("/track", response_model=ToolCallTrackResponse)
def track_endpoint(request: ToolCallTrackRequest) -> ToolCallTrackResponse:
    _set_span_attributes()
    total_cost = track_tool_call(request.trace_id, request.span_id, request.cost)
    return ToolCallTrackResponse(total_cost=total_cost)

@router.post("/clear", response_model=ToolCallClearResponse)
def clear_endpoint() -> ToolCallClearResponse:
    _set_span_attributes()
    clear_tool_call_tracker()
    return ToolCallClearResponse(success=True)
