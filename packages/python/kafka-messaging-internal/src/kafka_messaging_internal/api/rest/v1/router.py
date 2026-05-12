"""FastAPI router for v1 API - ZERO domain logic."""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from opentelemetry import trace, propagate
from opentelemetry.trace import SpanKind, Status, StatusCode

from kafka_messaging_internal.features.event_processing.index import create_event_processing
from kafka_messaging_internal.features.schema_registry.index import create_schema_registry
from kafka_messaging_internal.features.database_operations.index import create_database_operations
from kafka_messaging_internal.shared.errors.exceptions import BaseError
from kafka_messaging_internal.shared.di.container import get_container
from kafka_messaging_internal.shared.di.service_registration import register_production_services


security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager - initialize tracing first."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("application_startup") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api_startup",
            "api.version": "v1",
            "deployment.env": get_container().get_config().database_type
        })
        
        try:
            # Register production services
            register_production_services()
            span.set_attribute("services.registered", "true")
            
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
    
    yield
    
    # Cleanup on shutdown
    with tracer.start_as_current_span("application_shutdown") as shutdown_span:
        shutdown_span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api_shutdown"
        })
        shutdown_span.set_status(Status(StatusCode.OK))


# Feature instances will be created lazily
_event_processing = None
_schema_registry = None
_database_operations = None


def get_event_processing():
    """Get event processing instance (lazy initialization with tracing)."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("feature_initialization") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "event_processing",
            "api.version": "v1"
        })
        
        try:
            if os.getenv('DEPLOYMENT_ENV') == 'test':
                return create_event_processing()
                
            global _event_processing
            if _event_processing is None:
                _event_processing = create_event_processing()
                span.set_attribute("feature.initialized", "true")
            else:
                span.set_attribute("feature.cached", "true")
            
            span.set_status(Status(StatusCode.OK))
            return _event_processing
            
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def get_schema_registry():
    """Get schema registry instance (lazy initialization with tracing)."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("feature_initialization") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "schema_registry",
            "api.version": "v1"
        })
        
        try:
            if os.getenv('DEPLOYMENT_ENV') == 'test':
                return create_schema_registry()
                
            global _schema_registry
            if _schema_registry is None:
                _schema_registry = create_schema_registry()
                span.set_attribute("feature.initialized", "true")
            else:
                span.set_attribute("feature.cached", "true")
            
            span.set_status(Status(StatusCode.OK))
            return _schema_registry
            
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def get_database_operations():
    """Get database operations instance (lazy initialization with tracing)."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("feature_initialization") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "database_operations",
            "api.version": "v1"
        })
        
        try:
            if os.getenv('DEPLOYMENT_ENV') == 'test':
                return create_database_operations()
                
            global _database_operations
            if _database_operations is None:
                _database_operations = create_database_operations()
                span.set_attribute("feature.initialized", "true")
            else:
                span.set_attribute("feature.cached", "true")
            
            span.set_status(Status(StatusCode.OK))
            return _database_operations
            
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


# Create API router
api_router = APIRouter()


# Database endpoints
@api_router.post("/database/events", tags=["Database"])
async def store_event(request_data: dict, _=Depends(security)):
    """Store single event."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.store_event", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "POST",
            "http.route": "/database/events",
            "event.topic": request_data.get('topic', 'unknown')
        })
        
        try:
            # Edge case validation
            if not request_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request data cannot be empty"
                )
            
            topic = request_data.get('topic')
            if not topic or not topic.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Event topic cannot be empty", "code": "VALIDATION_ERROR"}
                )
            
            value = request_data.get('value')
            if not value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Event value cannot be empty", "code": "VALIDATION_ERROR"}
                )
            
            result = await get_event_processing().process_event(request_data)
            
            span.set_attributes({
                "http.status_code": "200",
                "processing.status": "success" if result.get("success") else "failed"
            })
            span.set_status(Status(StatusCode.OK))
            
            return result
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.get("/database/events/{event_id}", tags=["Database"])
async def get_event(event_id: str, _=Depends(security)):
    """Get event by ID."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.get_event", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/database/events/{event_id}",
            "event.id": event_id
        })
        
        try:
            result = await get_event_processing().get_event(event_id)
            
            span.set_attributes({
                "http.status_code": "200" if result else "404",
                "event.found": "true" if result else "false"
            })
            
            if result:
                span.set_status(Status(StatusCode.OK))
                return result
            else:
                span.set_status(Status(StatusCode.OK))
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found"
                )
                
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.get("/database/events", tags=["Database"])
async def query_events(topic: Optional[str] = None, limit: int = 100, offset: int = 0, _=Depends(security)):
    """Query events with pagination."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.query_events", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/database/events",
            "query.topic": topic or "all",
            "query.limit": str(limit),
            "query.offset": str(offset)
        })
        
        try:
            # Edge case validation
            if limit <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Limit must be greater than 0"
                )
            if offset < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Offset cannot be negative"
                )
            if limit > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Limit cannot exceed 1000"
                )
            
            filters = {"topic": topic, "limit": limit, "offset": offset}
            result = await get_event_processing().query_events(filters)
            
            span.set_attributes({
                "http.status_code": "200",
                "query.result_count": str(len(result)),
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return {
                "events": [event.to_dict() if hasattr(event, 'to_dict') else event for event in result],
                "count": len(result),
                "has_more": len(result) == limit,
                "filters": filters
            }
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.post("/database/events/batch", tags=["Database"])
async def store_events_batch(request_data: dict, _=Depends(security)):
    """Store multiple events in batch."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.store_events_batch", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "POST",
            "http.route": "/database/events/batch"
        })
        
        try:
            # Edge case validation
            if not request_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request data cannot be empty"
                )
            
            events = request_data.get("records", [])
            if not events:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Events records cannot be empty"
                )
            
            if len(events) > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Batch size cannot exceed 1000"
                )
            
            span.set_attribute("batch.size", str(len(events)))
            
            result = await get_event_processing().process_events_batch(events)
            
            # Transform list response to dict format for contract tests
            event_ids = []
            success = True
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        if item.get("success") and item.get("event_id"):
                            event_ids.append(item["event_id"])
                        elif item.get("error"):
                            success = False
                
                response_dict = {
                    "event_ids": event_ids,
                    "count": len(event_ids),
                    "success": success
                }
            else:
                response_dict = result
            
            event_ids = response_dict.get("event_ids", [])
            span.set_attributes({
                "http.status_code": "200",
                "batch.successful_count": str(response_dict.get("successful_count", len(event_ids))),
                "batch.failed_count": str(response_dict.get("failed_count", 0)),
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return response_dict
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.get("/database/offsets", tags=["Database"])
async def get_consumer_offsets(consumer_group: str, topic: Optional[str] = None, _=Depends(security)):
    """Get consumer offsets."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.get_consumer_offsets", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/database/offsets",
            "consumer.group": consumer_group,
            "consumer.topic": topic or "all"
        })
        
        try:
            # Edge case validation
            if not consumer_group or not consumer_group.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Consumer group cannot be empty"
                )
            
            filters = {"consumer_group": consumer_group, "topic": topic}
            result = await get_event_processing().get_consumer_offsets(filters)
            
            span.set_attributes({
                "http.status_code": "200",
                "query.result_count": str(result.get("count", 0)),
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return result
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.post("/database/offsets", tags=["Database"])
async def update_consumer_offset(request_data: dict, _=Depends(security)):
    """Update consumer offset."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.update_consumer_offset", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "POST",
            "http.route": "/database/offsets",
            "consumer.group": request_data.get('consumer_group', 'unknown'),
            "consumer.topic": request_data.get('topic', 'unknown')
        })
        
        try:
            # Edge case validation
            if not request_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request data cannot be empty"
                )
            
            result = await get_event_processing().update_consumer_offset(request_data)
            
            # Ensure response is always a flat dict for contract compliance
            if hasattr(result, 'to_dict'):
                response_dict = result.to_dict()
                # Ensure required fields are at top level for contract compliance
                if hasattr(result, 'metadata') and result.metadata:
                    response_dict.update(result.metadata)
            elif isinstance(result, dict):
                response_dict = result
            else:
                # Fallback: create flat dict from ProcessingResult
                response_dict = {
                    "success": getattr(result, 'success', False),
                    "consumer_group": request_data.get("consumer_group"),
                    "topic": request_data.get("topic"),
                    "partition": request_data.get("partition", 0),
                    "offset": request_data.get("offset", 0),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if hasattr(result, 'error') and result.error:
                    response_dict["error"] = result.error
            
            # Ensure response_dict is always a dict for subsequent operations
            if not isinstance(response_dict, dict):
                response_dict = dict(response_dict) if hasattr(response_dict, '__iter__') else {}
            
            # Double-check that required fields exist for contract compliance
            if 'consumer_group' not in response_dict:
                response_dict['consumer_group'] = request_data.get("consumer_group")
            if 'topic' not in response_dict:
                response_dict['topic'] = request_data.get("topic")
            if 'partition' not in response_dict:
                response_dict['partition'] = request_data.get("partition", 0)
            if 'offset' not in response_dict:
                response_dict['offset'] = request_data.get("offset", 0)
            if 'updated_at' not in response_dict:
                response_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            span.set_attributes({
                "http.status_code": "200",
                "processing.status": "success" if response_dict.get("success") else "failed"
            })
            span.set_status(Status(StatusCode.OK))
            
            return response_dict
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


# Schema Registry endpoints
@api_router.post("/schema-registry/schemas", tags=["Schema Registry"])
async def register_schema(request_data: dict, _=Depends(security)):
    """Register new schema."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.register_schema", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "POST",
            "http.route": "/schema-registry/schemas",
            "schema.subject": request_data.get('subject', 'unknown')
        })
        
        try:
            # Edge case validation
            if not request_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request data cannot be empty"
                )
            
            subject = request_data.get('subject')
            if not subject or not subject.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Schema subject cannot be empty", "code": "VALIDATION_ERROR"}
                )
            
            schema_def = request_data.get('schema')
            if not schema_def or not schema_def.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Schema definition cannot be empty", "code": "VALIDATION_ERROR"}
                )
            
            # Validate JSON format
            try:
                import json
                json.loads(schema_def)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Invalid JSON schema format", "code": "VALIDATION_ERROR"}
                )
            
            schema_type = request_data.get('schema_type')
            if not schema_type or not schema_type.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Schema type cannot be empty", "code": "VALIDATION_ERROR"}
                )
            
            result = await get_schema_registry().register_schema(request_data)
            
            # Check if registration failed
            if hasattr(result, 'success') and not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": result.error or "Schema registration failed", "code": "REGISTRATION_ERROR"}
                )
            
            span.set_attributes({
                "http.status_code": "200",
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return result
            
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(Status(StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.get("/schema-registry/schemas", tags=["Schema Registry"])
async def list_subjects(_=Depends(security)):
    """List all schema subjects."""
    try:
        subjects = await get_schema_registry().list_subjects()
        return {"subjects": subjects}
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/schema-registry/schemas/{subject}", tags=["Schema Registry"])
async def get_schema_by_subject(subject: str, version: Optional[int] = None, _=Depends(security)):
    """Get schema by subject and version."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.get_schema_by_subject", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/schema-registry/schemas/{subject}",
            "schema.subject": subject
        })
        
        try:
            result = await get_schema_registry().get_schema_by_subject(subject, version)
            
            span.set_attributes({
                "http.status_code": "200" if result else "404",
                "schema.found": "true" if result else "false"
            })
            
            if result:
                span.set_status(trace.Status(trace.StatusCode.OK))
                return result
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Schema not found"
                )
                
        except BaseError as e:
            span.set_attributes({
                "http.status_code": str(e.http_status),
                "error.code": e.code,
                "processing.status": "business_error"
            })
            span.set_status(trace.Status(trace.StatusCode.ERROR, e.message))
            raise HTTPException(
                status_code=e.http_status,
                detail={"error": e.message, "code": e.code, "details": e.details}
            )
        
        except HTTPException:
            raise
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Internal server error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


@api_router.post("/schema-registry/compatibility", tags=["Schema Registry"])
async def check_compatibility(request_data: dict, _=Depends(security)):
    """Check schema compatibility."""
    try:
        return await get_schema_registry().check_compatibility_api(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.put("/schema-registry/compatibility/{subject}", tags=["Schema Registry"])
async def update_compatibility(subject: str, request_data: dict, _=Depends(security)):
    """Update compatibility level for subject."""
    try:
        compatibility = request_data.get("compatibility", "")
        return await get_schema_registry().update_compatibility_api(subject, compatibility)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/schema-registry/serialize", tags=["Schema Registry"])
async def serialize_data(request_data: dict, _=Depends(security)):
    """Serialize data using schema."""
    try:
        return await get_schema_registry().serialize_data(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.post("/schema-registry/deserialize", tags=["Schema Registry"])
async def deserialize_data(request_data: dict, _=Depends(security)):
    """Deserialize data using schema."""
    try:
        return await get_schema_registry().deserialize_data(request_data)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


# Database Operations endpoints
@api_router.get("/database/count", tags=["Database"])
async def get_event_count(topic: Optional[str] = None, _=Depends(security)):
    """Get event count with optional topic filter."""
    try:
        filters = {"topic": topic}
        return await get_database_operations().get_event_count(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.delete("/database/events/by-topic/{topic}", tags=["Database"])
async def delete_events_by_topic(topic: str, _=Depends(security)):
    """Delete events by topic."""
    try:
        return await get_database_operations().delete_events_by_topic(topic)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


@api_router.get("/database/unprocessed", tags=["Database"])
async def get_unprocessed_events(limit: int = 100, _=Depends(security)):
    """Get unprocessed events."""
    try:
        filters = {"limit": limit}
        return await get_database_operations().get_unprocessed_events(filters)
    except BaseError as e:
        raise HTTPException(
            status_code=e.http_status,
            detail={"error": e.message, "code": e.code, "details": e.details}
        )


# Health endpoints
@api_router.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.health_check", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/health"
        })
        
        try:
            health_data = {
                "status": "healthy",
                "service": "kafka-messaging-internal",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            span.set_attributes({
                "http.status_code": "200",
                "health.status": "healthy",
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return health_data
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "health.status": "unhealthy",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Health check failed"))
            
            return {
                "status": "unhealthy",
                "service": "kafka-messaging-internal",
                "version": "1.0.0",
                "error": "Health check failed"
            }


@api_router.get("/", tags=["Health"])
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint with API info."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.root", kind=SpanKind.SERVER) as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "api",
            "api.version": "v1",
            "http.method": "GET",
            "http.route": "/"
        })
        
        try:
            root_data = {
                "message": "Kafka Messaging Internal API",
                "version": "1.0.0",
                "docs": "/docs",
                "redoc": "/redoc"
            }
            
            span.set_attributes({
                "http.status_code": "200",
                "processing.status": "success"
            })
            span.set_status(Status(StatusCode.OK))
            
            return root_data
            
        except Exception as e:
            span.record_error(e)
            span.set_attributes({
                "http.status_code": "500",
                "error.type": "InternalServerError"
            })
            span.set_status(Status(StatusCode.ERROR, "Root endpoint failed"))
            
            return {
                "message": "Kafka Messaging Internal API",
                "version": "1.0.0",
                "error": "Service unavailable"
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
