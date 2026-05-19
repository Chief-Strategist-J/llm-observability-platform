from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Union, List, Dict, Any
import os
from opentelemetry import trace
from .....features.pii_injection_scan.index import scan_prompt

router = APIRouter(prefix="/pii-injection", tags=["PII & Injection Scan"])

class PiiInjectionScanRequest(BaseModel):
    prompt: Union[str, List[Dict[str, Any]]]

class PiiInjectionScanResponse(BaseModel):
    pii_detected: bool
    injection_attempt: bool

def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "pii_injection_scan")

@router.post("/scan", response_model=PiiInjectionScanResponse)
def scan(request: PiiInjectionScanRequest) -> PiiInjectionScanResponse:
    _set_span_attributes()
    try:
        pii, inj = scan_prompt(request.prompt)
        span = trace.get_current_span()
        span.set_attribute("llm.pii_detected", pii)
        span.set_attribute("llm.injection_attempt", inj)
        return PiiInjectionScanResponse(pii_detected=pii, injection_attempt=inj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
