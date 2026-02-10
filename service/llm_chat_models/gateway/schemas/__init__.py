from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ModelInfoResponse(BaseModel):
    name: str
    description: str
    parameters: str
    size: str
    family: str
    downloaded: bool


class ModelStatusResponse(BaseModel):
    name: str
    status: str
    backend: str
    error: Optional[str] = None


class SimpleResponse(BaseModel):
    success: bool
    message: str
