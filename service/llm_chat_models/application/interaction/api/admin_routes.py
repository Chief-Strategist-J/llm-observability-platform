import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query

from ...data.model_repository import model_repository
from ...data.endpoint_repository import endpoint_repository
from ...data.schema_registry import schema_registry
from ...data.schemas import (
    AIModelCreate, AIModelUpdate, AIModelResponse, AIModelListResponse,
    APIEndpointCreate, APIEndpointUpdate, APIEndpointResponse, APIEndpointListResponse,
    TestRequest, TestResponse, SimpleResponse, SchemaArtifact, SchemaResponse, SchemaListResponse
)
from ...core.generation.request_handler import request_handler
from ...core.telemetry.logger import log_event, get_tracer, trace_with_details

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.post("/models", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def create_model(model: AIModelCreate):
    logger.info("event=api_create_model name=%s provider=%s", model.name, model.provider)
    log_event("admin_create_model", name=model.name, provider=model.provider.value)
    existing = model_repository.get_model_by_name(model.name)
    if existing:
        logger.error("event=api_create_model_error reason=duplicate_name name=%s", model.name)
        raise HTTPException(status_code=400, detail=f"Model with name '{model.name}' already exists")
    model_data = model.model_dump()
    model_data["provider"] = model.provider.value
    model_id = model_repository.create_model(model_data)
    logger.info("event=api_create_model_success id=%s", model_id)
    return {"success": True, "id": model_id, "message": f"Model '{model.name}' created successfully"}


@admin_router.get("/models", response_model=AIModelListResponse)
@trace_with_details(get_tracer())
async def list_models(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), is_active: Optional[bool] = None, provider: Optional[str] = None):
    logger.info("event=api_list_models page=%d limit=%d is_active=%s provider=%s", page, limit, is_active, provider)
    log_event("admin_list_models", page=page, limit=limit)
    filter_query = {}
    if is_active is not None:
        filter_query["is_active"] = is_active
    if provider:
        filter_query["provider"] = provider
    result = model_repository.list_models(filter_query=filter_query, page=page, limit=limit)
    logger.info("event=api_list_models_success count=%d total=%d", len(result["items"]), result["total_count"])
    return result


@admin_router.get("/models/{model_id}", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def get_model(model_id: str):
    logger.info("event=api_get_model id=%s", model_id)
    log_event("admin_get_model", model_id=model_id)
    model = model_repository.get_model_by_id(model_id)
    if not model:
        logger.error("event=api_get_model_error reason=not_found id=%s", model_id)
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    logger.info("event=api_get_model_success id=%s", model_id)
    return model


@admin_router.put("/models/{model_id}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def update_model(model_id: str, model: AIModelUpdate):
    logger.info("event=api_update_model id=%s", model_id)
    log_event("admin_update_model", model_id=model_id)
    existing = model_repository.get_model_by_id(model_id)
    if not existing:
        logger.error("event=api_update_model_error reason=not_found id=%s", model_id)
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    update_data = model.model_dump(exclude_unset=True)
    if "provider" in update_data and update_data["provider"]:
        update_data["provider"] = update_data["provider"].value
    success = model_repository.update_model(model_id, update_data)
    logger.info("event=api_update_model_result id=%s success=%s", model_id, success)
    return SimpleResponse(success=success, message="Model updated successfully" if success else "No changes made")


@admin_router.delete("/models/{model_id}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def delete_model(model_id: str):
    logger.info("event=api_delete_model id=%s", model_id)
    log_event("admin_delete_model", model_id=model_id)
    existing = model_repository.get_model_by_id(model_id)
    if not existing:
        logger.error("event=api_delete_model_error reason=not_found id=%s", model_id)
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    endpoints = endpoint_repository.get_endpoints_by_model(model_id)
    if endpoints:
        logger.error("event=api_delete_model_error reason=has_endpoints id=%s count=%d", model_id, len(endpoints))
        raise HTTPException(status_code=400, detail=f"Cannot delete model with {len(endpoints)} linked endpoints")
    success = model_repository.delete_model(model_id)
    logger.info("event=api_delete_model_result id=%s success=%s", model_id, success)
    return SimpleResponse(success=success, message="Model deleted successfully" if success else "Failed to delete model")


@admin_router.post("/models/{model_id}/test", response_model=TestResponse)
@trace_with_details(get_tracer())
async def test_model(model_id: str, request: TestRequest):
    logger.info("event=api_test_model id=%s", model_id)
    log_event("admin_test_model", model_id=model_id)
    result = await request_handler.test_model(
        model_id=model_id,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    logger.info("event=api_test_model_result id=%s success=%s latency_ms=%.2f", model_id, result["success"], result.get("latency_ms", 0))
    return TestResponse(**result)


@admin_router.post("/endpoints", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def create_endpoint(endpoint: APIEndpointCreate):
    logger.info("event=api_create_endpoint name=%s path=%s", endpoint.name, endpoint.endpoint_path)
    log_event("admin_create_endpoint", name=endpoint.name, path=endpoint.endpoint_path)
    existing_name = endpoint_repository.get_endpoint_by_name(endpoint.name)
    if existing_name:
        logger.error("event=api_create_endpoint_error reason=duplicate_name name=%s", endpoint.name)
        raise HTTPException(status_code=400, detail=f"Endpoint with name '{endpoint.name}' already exists")
    existing_path = endpoint_repository.get_endpoint_by_path(endpoint.endpoint_path)
    if existing_path:
        logger.error("event=api_create_endpoint_error reason=duplicate_path path=%s", endpoint.endpoint_path)
        raise HTTPException(status_code=400, detail=f"Endpoint with path '{endpoint.endpoint_path}' already exists")
    model = model_repository.get_model_by_id(endpoint.model_id)
    if not model:
        logger.error("event=api_create_endpoint_error reason=model_not_found model_id=%s", endpoint.model_id)
        raise HTTPException(status_code=400, detail=f"Model not found: {endpoint.model_id}")
    endpoint_data = endpoint.model_dump()
    endpoint_data["method"] = endpoint.method.value
    endpoint_data["request_template"] = endpoint.request_template.model_dump()
    endpoint_data["response_mapping"] = endpoint.response_mapping.model_dump()
    endpoint_id = endpoint_repository.create_endpoint(endpoint_data)
    logger.info("event=api_create_endpoint_success id=%s", endpoint_id)
    return {"success": True, "id": endpoint_id, "message": f"Endpoint '{endpoint.name}' created successfully"}


@admin_router.get("/endpoints", response_model=APIEndpointListResponse)
@trace_with_details(get_tracer())
async def list_endpoints(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), is_active: Optional[bool] = None, model_id: Optional[str] = None):
    logger.info("event=api_list_endpoints page=%d limit=%d is_active=%s model_id=%s", page, limit, is_active, model_id)
    log_event("admin_list_endpoints", page=page, limit=limit)
    filter_query = {}
    if is_active is not None:
        filter_query["is_active"] = is_active
    if model_id:
        filter_query["model_id"] = model_id
    result = endpoint_repository.list_endpoints(filter_query=filter_query, page=page, limit=limit)
    logger.info("event=api_list_endpoints_success count=%d total=%d", len(result["items"]), result["total_count"])
    return result


@admin_router.get("/endpoints/{endpoint_id}", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def get_endpoint(endpoint_id: str):
    logger.info("event=api_get_endpoint id=%s", endpoint_id)
    log_event("admin_get_endpoint", endpoint_id=endpoint_id)
    endpoint = endpoint_repository.get_endpoint_by_id(endpoint_id)
    if not endpoint:
        logger.error("event=api_get_endpoint_error reason=not_found id=%s", endpoint_id)
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_id}")
    logger.info("event=api_get_endpoint_success id=%s", endpoint_id)
    return endpoint


@admin_router.put("/endpoints/{endpoint_id}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def update_endpoint(endpoint_id: str, endpoint: APIEndpointUpdate):
    logger.info("event=api_update_endpoint id=%s", endpoint_id)
    log_event("admin_update_endpoint", endpoint_id=endpoint_id)
    existing = endpoint_repository.get_endpoint_by_id(endpoint_id)
    if not existing:
        logger.error("event=api_update_endpoint_error reason=not_found id=%s", endpoint_id)
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_id}")
    update_data = endpoint.model_dump(exclude_unset=True)
    if "method" in update_data and update_data["method"]:
        update_data["method"] = update_data["method"].value
    if "request_template" in update_data and update_data["request_template"]:
        update_data["request_template"] = update_data["request_template"].model_dump()
    if "response_mapping" in update_data and update_data["response_mapping"]:
        update_data["response_mapping"] = update_data["response_mapping"].model_dump()
    success = endpoint_repository.update_endpoint(endpoint_id, update_data)
    logger.info("event=api_update_endpoint_result id=%s success=%s", endpoint_id, success)
    return SimpleResponse(success=success, message="Endpoint updated successfully" if success else "No changes made")


@admin_router.delete("/endpoints/{endpoint_id}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def delete_endpoint(endpoint_id: str):
    logger.info("event=api_delete_endpoint id=%s", endpoint_id)
    log_event("admin_delete_endpoint", endpoint_id=endpoint_id)
    existing = endpoint_repository.get_endpoint_by_id(endpoint_id)
    if not existing:
        logger.error("event=api_delete_endpoint_error reason=not_found id=%s", endpoint_id)
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_id}")
    success = endpoint_repository.delete_endpoint(endpoint_id)
    logger.info("event=api_delete_endpoint_result id=%s success=%s", endpoint_id, success)
    return SimpleResponse(success=success, message="Endpoint deleted successfully" if success else "Failed to delete endpoint")


@admin_router.post("/schemas", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def register_schema(schema: SchemaArtifact):
    logger.info("event=api_register_schema artifact_id=%s type=%s", schema.artifact_id, schema.artifact_type)
    log_event("admin_register_schema", artifact_id=schema.artifact_id)
    result = await schema_registry.register_schema(
        artifact_id=schema.artifact_id,
        content=schema.content,
        artifact_type=schema.artifact_type,
        description=schema.description
    )
    logger.info("event=api_register_schema_success artifact_id=%s", schema.artifact_id)
    return {"success": True, "artifact_id": schema.artifact_id, "version": result.get("version")}


@admin_router.get("/schemas", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def list_schemas():
    logger.info("event=api_list_schemas")
    log_event("admin_list_schemas")
    artifacts = await schema_registry.list_schemas()
    logger.info("event=api_list_schemas_success count=%d", len(artifacts))
    return {"artifacts": artifacts, "count": len(artifacts)}


@admin_router.get("/schemas/{artifact_id}", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def get_schema(artifact_id: str, version: Optional[str] = None):
    logger.info("event=api_get_schema artifact_id=%s version=%s", artifact_id, version)
    log_event("admin_get_schema", artifact_id=artifact_id)
    result = await schema_registry.get_schema(artifact_id, version)
    logger.info("event=api_get_schema_success artifact_id=%s", artifact_id)
    return result


@admin_router.put("/schemas/{artifact_id}", response_model=Dict[str, Any])
@trace_with_details(get_tracer())
async def update_schema(artifact_id: str, schema: SchemaArtifact):
    logger.info("event=api_update_schema artifact_id=%s", artifact_id)
    log_event("admin_update_schema", artifact_id=artifact_id)
    result = await schema_registry.update_schema(
        artifact_id=artifact_id,
        content=schema.content,
        artifact_type=schema.artifact_type
    )
    logger.info("event=api_update_schema_success artifact_id=%s version=%s", artifact_id, result.get("version"))
    return {"success": True, "artifact_id": artifact_id, "version": result.get("version")}


@admin_router.delete("/schemas/{artifact_id}", response_model=SimpleResponse)
@trace_with_details(get_tracer())
async def delete_schema(artifact_id: str):
    logger.info("event=api_delete_schema artifact_id=%s", artifact_id)
    log_event("admin_delete_schema", artifact_id=artifact_id)
    success = await schema_registry.delete_schema(artifact_id)
    logger.info("event=api_delete_schema_result artifact_id=%s success=%s", artifact_id, success)
    return SimpleResponse(success=success, message="Schema deleted successfully" if success else "Failed to delete schema")


@admin_router.get("/health", response_model=Dict[str, Any])
async def admin_health():
    logger.info("event=api_admin_health")
    schema_healthy = await schema_registry.health_check()
    return {
        "status": "healthy",
        "components": {
            "schema_registry": "healthy" if schema_healthy else "unhealthy"
        }
    }
