import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.telemetry.metrics import REQUEST_COUNT, REQUEST_LATENCY

class CorrelationAndTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get(HTTP_CONSTANTS.HEADER_X_CORRELATION_ID, str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        response.headers[HTTP_CONSTANTS.HEADER_X_CORRELATION_ID] = correlation_id
        
        endpoint = request.url.path
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
        
        return response
