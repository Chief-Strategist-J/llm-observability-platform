import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...data.endpoint_repository import endpoint_repository
from ...data.schemas import DynamicEndpointRequest, DynamicEndpointResponse
from ...core.generation.request_handler import request_handler
from ...core.telemetry.logger import log_event, get_tracer, trace_with_details

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dynamic_router = APIRouter(prefix="/api/v1", tags=["Dynamic Endpoints"])


@dynamic_router.post("/{endpoint_path:path}", response_model=DynamicEndpointResponse)
@trace_with_details(get_tracer())
async def execute_dynamic_endpoint(endpoint_path: str, request: DynamicEndpointRequest):
    logger.info("event=dynamic_endpoint_request path=%s", endpoint_path)
    log_event("dynamic_endpoint_request", path=endpoint_path)
    endpoint = endpoint_repository.get_endpoint_by_path(endpoint_path)
    if not endpoint:
        logger.error("event=dynamic_endpoint_error reason=not_found path=%s", endpoint_path)
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_path}")
    if not endpoint.get("is_active"):
        logger.error("event=dynamic_endpoint_error reason=inactive path=%s", endpoint_path)
        raise HTTPException(status_code=400, detail=f"Endpoint is not active: {endpoint_path}")
    request_data = {"prompt": request.prompt}
    if request.context:
        request_data.update(request.context)
    result = await request_handler.execute_request(endpoint["_id"], request_data)
    if not result["success"]:
        logger.error("event=dynamic_endpoint_execution_error path=%s error=%s", endpoint_path, result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "Request execution failed"))
    logger.info("event=dynamic_endpoint_success path=%s model=%s", endpoint_path, result.get("model_name"))
    return DynamicEndpointResponse(
        success=True,
        endpoint_name=result.get("endpoint_name", ""),
        model_name=result.get("model_name", ""),
        response=result.get("response")
    )


@dynamic_router.get("/endpoints", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def list_available_endpoints():
    logger.info("event=list_available_endpoints")
    log_event("list_available_endpoints")
    endpoints = endpoint_repository.get_active_endpoints()
    result = []
    for ep in endpoints:
        result.append({
            "name": ep["name"],
            "path": f"/api/v1/{ep['endpoint_path']}",
            "description": ep.get("description", ""),
            "method": ep.get("method", "POST")
        })
    logger.info("event=list_available_endpoints_success count=%d", len(result))
    return {"endpoints": result, "count": len(result)}
