from pydantic import BaseModel, Field
from typing import List, Optional

class VerifyApiKeyRequest(BaseModel):
    key: str = Field(..., description="Raw API key string to verify")
    required_permission: Optional[str] = Field(None, description="Optional permission identifier")

class VerifyApiKeyResponse(BaseModel):
    valid: bool
    org_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class GenerateApiKeyRequest(BaseModel):
    name: str
    org_id: str
    permissions: List[str] = Field(default_factory=lambda: ["spans:write", "spans:read"])

class GenerateApiKeyResponse(BaseModel):
    key: str
    key_hash: str
    org_id: str
