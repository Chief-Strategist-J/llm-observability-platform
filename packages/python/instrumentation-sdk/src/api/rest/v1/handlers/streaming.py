from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
from opentelemetry import trace
from .....features.streaming.index import llm_streaming_span, wrap_async_stream

router = APIRouter(prefix="/streaming", tags=["Streaming"])

class TestStreamRequest(BaseModel):
    provider: str
    chunks: Optional[List[str]] = None

def _set_span_attributes():
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "streaming")

async def mock_async_stream(chunks: List[str]):
    for chunk in chunks:
        await asyncio.sleep(0.01)
        yield chunk

@router.post("/test-stream-call")
async def test_stream_call(request: TestStreamRequest):
    _set_span_attributes()
    try:
        chunks = request.chunks
        if not chunks:
            chunks = ["Hello ", "there! ", "This ", "is ", "a ", "mock ", "stream."]
        
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider=request.provider,
            model="test-stream-model",
            prompt="Triggered via API verification endpoint",
        )
        
        wrapped_stream = wrap_async_stream(
            mock_async_stream(chunks),
            span_context=span_ctx,
            model="test-stream-model"
        )
        
        async def event_generator():
            async with span_ctx:
                async for chunk in wrapped_stream:
                    yield f"data: {chunk}\n\n"
                    
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
