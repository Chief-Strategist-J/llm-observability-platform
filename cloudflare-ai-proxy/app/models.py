from pydantic import BaseModel, Field
from typing import Optional

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Input prompt for the AI model", min_length=1)
    
    # Optional inference parameter overrides
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate", gt=0, le=2048)
    temperature: Optional[float] = Field(None, description="Sampling temperature", ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, description="Top-p sampling parameter", ge=0.0, le=1.0)

class GenerateResponse(BaseModel):
    """Response model for text generation"""
    model_id: str = Field(..., description="Model used for generation")
    response: str = Field(..., description="Generated text response")
    prompt: str = Field(..., description="Original prompt")
    success: bool = Field(default=True, description="Whether generation was successful")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_id: str
    version: str
    cloudflare_api_healthy: bool
