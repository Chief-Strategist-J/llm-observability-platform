from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from ...core.generation.manager import ModelManager
from .schemas import (
    ModelInfoResponse, 
    ModelStatusResponse, 
    ChatRequest, 
    ChatResponse, 
    SimpleResponse
)
from ...core.telemetry.logger import log_event, get_tracer, trace_with_details

router = APIRouter()
manager = ModelManager()

@router.get("/models", response_model=List[ModelInfoResponse])
@trace_with_details(get_tracer())
async def list_models():
    log_event("api_list_models")
    return await manager.list_available_models()

@router.get("/models/{name}", response_model=ModelStatusResponse)
@trace_with_details(get_tracer())
async def get_model_status(name: str):
    log_event("api_get_model_status", model=name)
    status = await manager.get_model_status(name)
    if status.get("status") == "unknown_model":
        raise HTTPException(status_code=404, detail=f"Model {name} not found in registry")
    return status

@router.post("/models/{name}/download", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def download_model(name: str, background_tasks: BackgroundTasks):
    log_event("api_download_model_request", model=name)

    # Check if valid model first
    try:
        # We don't await download here, just trigger it
        background_tasks.add_task(manager.download_model, name)
        return SimpleResponse(success=True, message=f"Download started for {name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/models/{name}/start", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def start_model(name: str):
    log_event("api_start_model", model=name)
    try:
        success = await manager.start_model(name)
        if success:
            return SimpleResponse(success=True, message=f"Model {name} started")
        raise HTTPException(status_code=400, detail="Failed to start model")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/models/{name}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def delete_model(name: str):
    log_event("api_delete_model", model=name)
    try:
        success = await manager.delete_model(name)
        if success:
            return SimpleResponse(success=True, message=f"Model {name} deleted")
        raise HTTPException(status_code=500, detail="Failed to delete model")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/chat/completions", response_model=ChatResponse)
@trace_with_details(get_tracer())
async def chat_completions(request: ChatRequest):
    log_event("api_chat_completions", model=request.model)

    # Construct prompt from messages (simple concatenation for now)
    # Real implementation would use template based on model family
    prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])

    result = await manager.generate_response(
        model_name=request.model,
        prompt=prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )

    if "error" in result:
        log_event("api_chat_error", error=result["error"])
        raise HTTPException(status_code=500, detail=result["error"])

    return ChatResponse(
        id="chatcmpl-" + request.model, # distinct ID generation could be added
        created=0, # timestamp
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result.get("response", "")
            },
            "finish_reason": "stop"
        }],
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0} # Usage not returned by simple API yet
    )

# We need to import trace for get_current_span
from opentelemetry import trace
