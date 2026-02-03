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

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool = False
    options: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    model: str
    created_at: str
    message: Dict[str, str]
    done: bool

class SimpleResponse(BaseModel):
    success: bool
    message: str
