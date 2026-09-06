from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Union, List, Dict, Any
import os
from opentelemetry import trace
from .....features.token_counting.index import count_tokens

router = APIRouter(prefix="/token-counting", tags=["Token Counting"])

class TokenCountRequest(BaseModel):
    prompt: Union[str, List[Dict[str, Any]]]
    model: str

class TokenCountResponse(BaseModel):
    tokens: int
    method: str

def _set_span_attributes():
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "token_counting")

@router.post("/count", response_model=TokenCountResponse)
def count(request: TokenCountRequest):
    _set_span_attributes()
    try:
        tokens, method = count_tokens(request.prompt, request.model)
        return TokenCountResponse(tokens=tokens, method=method)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
