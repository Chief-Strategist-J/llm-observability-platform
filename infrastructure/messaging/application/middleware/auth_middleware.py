from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: Optional[str] = None, skip_paths: Optional[list] = None):
        super().__init__(app)
        self._api_key = api_key
        self._skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._should_skip(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        if not self._api_key:
            logger.warning("Auth middleware enabled but no API key configured")
            return await call_next(request)

        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if token == self._api_key:
                    return await call_next(request)

        if api_key_header and api_key_header == self._api_key:
            return await call_next(request)

        logger.warning(
            "Unauthorized access attempt",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client_host": request.client.host if request.client else None
            }
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials"
        )

    def _should_skip(self, path: str) -> bool:
        return any(path.startswith(skip) for skip in self._skip_paths)
