from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from opentelemetry import trace
from .....features.deterministic_sampling.index import should_sample

router = APIRouter(prefix="/sampling", tags=["Deterministic Sampling"])

class SamplingGateRequest(BaseModel):
    span_id: str

class SamplingGateResponse(BaseModel):
    is_sampled: bool

def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "deterministic_sampling")

@router.post("/should-sample", response_model=SamplingGateResponse)
def should_sample_endpoint(request: SamplingGateRequest) -> SamplingGateResponse:
    _set_span_attributes()
    try:
        sampled = should_sample(request.span_id)
        span = trace.get_current_span()
        span.set_attribute("llm.is_sampled", sampled)
        return SamplingGateResponse(is_sampled=sampled)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
