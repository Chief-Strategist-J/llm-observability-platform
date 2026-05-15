from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from opentelemetry import trace
from .....features.auto_instrumentation import (
    init_auto_instrumentation,
    uninstrument_all,
    detect_llm_call,
    trigger_test_call
)


router = APIRouter(prefix="/instrumentation", tags=["Instrumentation"])

class StatusResponse(BaseModel):
    success: bool
    message: str

class DetectionRequest(BaseModel):
    url: str
    body: str

class DetectionResponse(BaseModel):
    provider: str
    model: str

class TestCallRequest(BaseModel):
    method: str
    provider: str

def _set_span_attributes():
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "auto_instrumentation")


@router.post("/init", response_model=StatusResponse)
def init_instrumentation():
    _set_span_attributes()
    try:
        init_auto_instrumentation()
        return StatusResponse(success=True, message="Auto-instrumentation initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/uninstrument", response_model=StatusResponse)
def uninstrument():
    _set_span_attributes()
    try:
        uninstrument_all()
        return StatusResponse(success=True, message="All instrumentation disabled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect", response_model=DetectionResponse)
def detect(request: DetectionRequest):
    _set_span_attributes()
    result = detect_llm_call(request.url, request.body)
    return DetectionResponse(**result)




@router.post("/test-call", response_model=StatusResponse)
async def test_call(request: TestCallRequest):
    _set_span_attributes()
    result = await trigger_test_call(request.method, request.provider)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return StatusResponse(**result)

