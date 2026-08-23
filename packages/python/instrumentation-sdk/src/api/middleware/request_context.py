import time
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

IDEMPOTENCY_STORE: Dict[str, Dict[str, Any]] = {}

def generate_w3c_traceparent() -> str:
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    return f"00-{trace_id}-{span_id}-01"

def generate_identifier(prefix: str) -> str:
    timestamp_ms = int(time.time() * 1000)
    random_hex = uuid.uuid4().hex[:6]
    return f"{prefix}-{timestamp_ms}-{random_hex}"

class StandardRequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        current_span = trace.get_current_span()

        headers = request.headers
        traceparent = headers.get("traceparent") or generate_w3c_traceparent()
        request_id = headers.get("x-request-id") or generate_identifier("req")
        correlation_id = headers.get("x-correlation-id") or request_id
        causation_id = headers.get("x-causation-id") or request_id
        idempotency_key = headers.get("x-idempotency-key") or request_id
        tenant_id = headers.get("x-tenant-id") or headers.get("x-org-id") or "tenant-default"

        request.state.traceparent = traceparent
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.causation_id = causation_id
        request.state.idempotency_key = idempotency_key
        request.state.tenant_id = tenant_id

        if current_span.is_recording():
            current_span.set_attribute("http.method", request.method)
            current_span.set_attribute("http.target", str(request.url.path))
            current_span.set_attribute("x-request-id", request_id)
            current_span.set_attribute("x-correlation-id", correlation_id)
            current_span.set_attribute("x-tenant-id", tenant_id)

        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if idempotency_key in IDEMPOTENCY_STORE:
                cached = IDEMPOTENCY_STORE[idempotency_key]
                res = JSONResponse(status_code=cached["statusCode"], content=cached["response"])
                res.headers["x-cache-hit"] = "true"
                res.headers["x-request-id"] = request_id
                res.headers["x-correlation-id"] = correlation_id
                res.headers["traceparent"] = traceparent
                return res

        try:
            response = await call_next(request)
            execution_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code >= 400:
                if current_span.is_recording():
                    current_span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                    current_span.set_attribute("error", True)
                    current_span.set_attribute("http.status_code", response.status_code)

                response.headers["x-request-id"] = request_id
                response.headers["x-correlation-id"] = correlation_id
                response.headers["traceparent"] = traceparent
                return response

            response_body = [chunk async for chunk in response.body_iterator]
            body_bytes = b"".join(response_body)

            try:
                raw_data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                raw_data = body_bytes.decode("utf-8")

            if isinstance(raw_data, dict) and "success" in raw_data and "meta" in raw_data:
                final_envelope = raw_data
            else:
                final_envelope = {
                    "success": True,
                    "statusCode": response.status_code,
                    "data": raw_data,
                    "meta": {
                        "requestId": request_id,
                        "correlationId": correlation_id,
                        "causationId": causation_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "executionTimeMs": execution_time_ms,
                    },
                }

            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                IDEMPOTENCY_STORE[idempotency_key] = {
                    "statusCode": response.status_code,
                    "response": final_envelope,
                }

            if current_span.is_recording():
                current_span.set_status(Status(StatusCode.OK))
                current_span.set_attribute("http.status_code", response.status_code)

            wrapped_response = JSONResponse(status_code=response.status_code, content=final_envelope)
            wrapped_response.headers["x-request-id"] = request_id
            wrapped_response.headers["x-correlation-id"] = correlation_id
            wrapped_response.headers["traceparent"] = traceparent
            return wrapped_response

        except Exception as exc:
            execution_time_ms = int((time.time() - start_time) * 1000)
            if current_span.is_recording():
                current_span.record_exception(exc)
                current_span.set_status(Status(StatusCode.ERROR, str(exc)))
                current_span.set_attribute("error", True)
                current_span.set_attribute("error.message", str(exc))
                current_span.set_attribute("http.status_code", 500)

            error_envelope = {
                "success": False,
                "statusCode": 500,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(exc),
                    "details": [],
                },
                "meta": {
                    "requestId": request_id,
                    "correlationId": correlation_id,
                    "causationId": causation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "executionTimeMs": execution_time_ms,
                },
            }
            err_response = JSONResponse(status_code=500, content=error_envelope)
            err_response.headers["x-request-id"] = request_id
            err_response.headers["x-correlation-id"] = correlation_id
            err_response.headers["traceparent"] = traceparent
            return err_response
