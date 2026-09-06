from fastapi import APIRouter
from pydantic import BaseModel
import os
from opentelemetry import trace
from .....features.spans.fallback_tracker import track_fallback, clear_fallback_tracker

router = APIRouter(prefix="/fallback", tags=["Fallback Tracking"])

class FallbackTrackRequest(BaseModel):
    trace_id: str
    model: str

class FallbackTrackResponse(BaseModel):
    retry_count: int
    attempted_models: list[str]

class FallbackClearResponse(BaseModel):
    success: bool

def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "fallback_tracking")

@router.post("/track", response_model=FallbackTrackResponse)
def track_endpoint(request: FallbackTrackRequest) -> FallbackTrackResponse:
    _set_span_attributes()
    retry_count, attempted_models = track_fallback(request.trace_id, request.model)
    return FallbackTrackResponse(retry_count=retry_count, attempted_models=attempted_models)

@router.post("/clear", response_model=FallbackClearResponse)
def clear_endpoint() -> FallbackClearResponse:
    _set_span_attributes()
    clear_fallback_tracker()
    return FallbackClearResponse(success=True)
