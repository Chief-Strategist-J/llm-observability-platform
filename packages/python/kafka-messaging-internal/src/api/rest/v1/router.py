"""FastAPI router for v1 API - ZERO domain logic."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from typing import Optional

from ...features.event_processing.index import create_event_processing
from ...features.schema_registry.index import create_schema_registry
from ...features.database_operations.index import create_database_operations
from ...shared.errors.exceptions import BaseError
from ...shared.di.container import get_container


security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager - initialize tracing first."""
    # OTEL tracer is initialized in main.py before this
    yield


# Create feature instances
event_processing = create_event_processing()
schema_registry = create_schema_registry()
database_operations = create_database_operations()


# Create API router
api_router = APIRouter()


# Database endpoints
@api_router.post("/database/events", tags=["Database"])
async def store_event(request_data: dict):
    """Store single event."""
    try:
        return event_processing.process_event(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/database/events", tags=["Database"])
async def query_events(topic: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Query events with pagination."""
    try:
        filters = {"topic": topic, "limit": limit, "offset": offset}
        return event_processing.query_events(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/database/events/batch", tags=["Database"])
async def store_events_batch(request_data: dict):
    """Store multiple events in batch."""
    try:
        return event_processing.process_events_batch(request_data.get("records", []))
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/database/offsets", tags=["Database"])
async def get_consumer_offsets(consumer_group: str, topic: Optional[str] = None):
    """Get consumer offsets."""
    try:
        filters = {"consumer_group": consumer_group, "topic": topic}
        return event_processing.get_consumer_offsets(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/database/offsets", tags=["Database"])
async def update_consumer_offset(request_data: dict):
    """Update consumer offset."""
    try:
        return event_processing.update_consumer_offset(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


# Schema Registry endpoints
@api_router.post("/schema-registry/schemas", tags=["Schema Registry"])
async def register_schema(request_data: dict):
    """Register new schema."""
    try:
        return schema_registry.register_schema(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/schema-registry/schemas", tags=["Schema Registry"])
async def list_subjects():
    """List all schema subjects."""
    try:
        return schema_registry.list_subjects()
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/schema-registry/schemas/{subject}", tags=["Schema Registry"])
async def get_schema_by_subject(subject: str, version: Optional[int] = None):
    """Get schema by subject and version."""
    try:
        return schema_registry.get_schema_by_subject(subject, version)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/schema-registry/compatibility", tags=["Schema Registry"])
async def check_compatibility(request_data: dict):
    """Check schema compatibility."""
    try:
        return schema_registry.check_compatibility(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.put("/schema-registry/compatibility/{subject}", tags=["Schema Registry"])
async def update_compatibility(subject: str, request_data: dict):
    """Update compatibility level for subject."""
    try:
        return schema_registry.update_compatibility(subject, request_data.get("compatibility"))
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/schema-registry/serialize", tags=["Schema Registry"])
async def serialize_data(request_data: dict):
    """Serialize data using schema."""
    try:
        return schema_registry.serialize_data(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/schema-registry/deserialize", tags=["Schema Registry"])
async def deserialize_data(request_data: dict):
    """Deserialize data using schema."""
    try:
        return schema_registry.deserialize_data(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


# Database Operations endpoints
@api_router.get("/database/count", tags=["Database"])
async def get_event_count(topic: Optional[str] = None):
    """Get event count with optional topic filter."""
    try:
        filters = {"topic": topic}
        return database_operations.get_event_count(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.delete("/database/events/by-topic/{topic}", tags=["Database"])
async def delete_events_by_topic(topic: str):
    """Delete events by topic."""
    try:
        return database_operations.delete_events_by_topic(topic)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/database/unprocessed", tags=["Database"])
async def get_unprocessed_events(limit: int = 100):
    """Get unprocessed events."""
    try:
        filters = {"limit": limit}
        return database_operations.get_unprocessed_events(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


# Health endpoints
@api_router.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "kafka-messaging-internal",
        "version": "1.0.0"
    }


@api_router.get("/", tags=["Health"])
@limiter.limit("100/minute")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Kafka Messaging Internal API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


def create_app():
    """Create FastAPI application with tracing and middleware."""
    from fastapi import FastAPI
    
    app = FastAPI(
        title="Kafka Messaging Internal API",
        description="REST API for messaging operations following hexagonal architecture",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    return app
