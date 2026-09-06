from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from src.features.api_keys.schema.api_key_schema import (
    VerifyApiKeyRequest,
    VerifyApiKeyResponse,
    GenerateApiKeyRequest,
    GenerateApiKeyResponse,
)
from src.features.api_keys.service import api_key_service

router = APIRouter(prefix="/auth/api-keys", tags=["Authentication"])

@router.post("/verify", response_model=VerifyApiKeyResponse)
def verify_api_key(
    payload: VerifyApiKeyRequest,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
):
    raw_key = payload.key or x_api_key
    if not raw_key and authorization and authorization.startswith("Bearer "):
        raw_key = authorization[7:].strip()

    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key credentials",
        )

    res = api_key_service.verify_key(raw_key, payload.required_permission)
    if not res.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    return res

@router.post("/generate", response_model=GenerateApiKeyResponse)
def generate_api_key(payload: GenerateApiKeyRequest):
    return api_key_service.generate_key(
        name=payload.name,
        org_id=payload.org_id,
        permissions=payload.permissions,
    )
