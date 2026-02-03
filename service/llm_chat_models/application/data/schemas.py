from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Unique model identifier")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human readable name")
    description: Optional[str] = Field(None, max_length=1000)
    provider: ProviderType = Field(..., description="AI provider type")
    base_url: str = Field(..., description="Base URL for API requests")
    api_key: Optional[str] = Field(None, description="API key if required")
    model_id: str = Field(..., description="Model identifier for the provider")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=128000)
    context_length: int = Field(4096, ge=1, le=200000)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    is_active: bool = Field(True)


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    provider: Optional[ProviderType] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    context_length: Optional[int] = Field(None, ge=1, le=200000)
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class AIModelResponse(AIModelBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class AIModelListResponse(BaseModel):
    items: List[AIModelResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int


class RequestTemplate(BaseModel):
    prompt_field: str = Field("prompt", description="Field name for prompt in request")
    system_prompt: Optional[str] = Field(None, description="Default system prompt")
    include_fields: List[str] = Field(default_factory=list)


class ResponseMapping(BaseModel):
    content_field: str = Field("response", description="Field to extract response from")


class APIEndpointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Unique endpoint identifier")
    description: Optional[str] = Field(None, max_length=1000)
    model_id: str = Field(..., description="Reference to AI model ID")
    endpoint_path: str = Field(..., min_length=1, max_length=200, description="URL path for the endpoint")
    method: HTTPMethod = Field(HTTPMethod.POST)
    request_template: RequestTemplate = Field(default_factory=RequestTemplate)
    response_mapping: ResponseMapping = Field(default_factory=ResponseMapping)
    rate_limit: int = Field(60, ge=1, le=10000, description="Requests per minute")
    is_active: bool = Field(True)


class APIEndpointCreate(APIEndpointBase):
    pass


class APIEndpointUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=1000)
    model_id: Optional[str] = None
    endpoint_path: Optional[str] = Field(None, min_length=1, max_length=200)
    method: Optional[HTTPMethod] = None
    request_template: Optional[RequestTemplate] = None
    response_mapping: Optional[ResponseMapping] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None


class APIEndpointResponse(APIEndpointBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class APIEndpointListResponse(BaseModel):
    items: List[APIEndpointResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    model: str = Field(..., description="Model name to use")
    messages: List[ChatMessage]
    stream: bool = Field(False)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    options: Optional[Dict[str, Any]] = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    created: int
    model: str
    choices: List[ChatChoice]
    usage: ChatUsage


class TestRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)


class TestResponse(BaseModel):
    success: bool
    model_name: str
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float


class SimpleResponse(BaseModel):
    success: bool
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class SchemaArtifact(BaseModel):
    artifact_id: str = Field(..., description="Unique schema identifier")
    group_id: str = Field(..., description="Group for the schema")
    version: Optional[str] = None
    artifact_type: str = Field("JSON", description="Schema type: JSON, AVRO, PROTOBUF, etc.")
    name: Optional[str] = None
    description: Optional[str] = None
    content: str = Field(..., description="Schema content as string")


class SchemaResponse(BaseModel):
    artifact_id: str
    group_id: str
    version: str
    artifact_type: str
    created_on: Optional[datetime] = None
    modified_on: Optional[datetime] = None


class SchemaListResponse(BaseModel):
    artifacts: List[SchemaResponse]
    count: int


class DynamicEndpointRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None
    stream: bool = Field(False)


class DynamicEndpointResponse(BaseModel):
    success: bool
    endpoint_name: str
    model_name: str
    response: Optional[str] = None
    error: Optional[str] = None
