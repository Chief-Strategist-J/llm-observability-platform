from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from gateway.schemas import ModelInfoResponse, ModelStatusResponse, SimpleResponse
from logic.models.manager import ModelManager
from telemetry.logger import log_event, get_tracer, trace_with_details

router = APIRouter(prefix="/models", tags=["models"])
manager = ModelManager()


@router.get("", response_model=List[ModelInfoResponse])
@trace_with_details(get_tracer())
async def list_models():
    log_event("api_list_models")
    return await manager.list_available_models()


@router.get("/{name}", response_model=ModelStatusResponse)
@trace_with_details(get_tracer())
async def get_model_status(name: str):
    log_event("api_get_model_status", model=name)
    status = await manager.get_model_status(name)
    if status.get("status") == "unknown_model":
        raise HTTPException(
            status_code=404, detail=f"Model {name} not found in registry"
        )
    return status


@router.post("/{name}/download", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def download_model(name: str, background_tasks: BackgroundTasks):
    log_event("api_download_model_request", model=name)
    try:
        background_tasks.add_task(manager.download_model, name)
        return SimpleResponse(
            success=True, message=f"Download started for {name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{name}/start", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def start_model(name: str):
    log_event("api_start_model", model=name)
    try:
        success = await manager.start_model(name)
        if success:
            return SimpleResponse(
                success=True, message=f"Model {name} started"
            )
        raise HTTPException(status_code=400, detail="Failed to start model")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{name}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def delete_model(name: str):
    log_event("api_delete_model", model=name)
    try:
        success = await manager.delete_model(name)
        if success:
            return SimpleResponse(
                success=True, message=f"Model {name} deleted"
            )
        raise HTTPException(status_code=500, detail="Failed to delete model")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
