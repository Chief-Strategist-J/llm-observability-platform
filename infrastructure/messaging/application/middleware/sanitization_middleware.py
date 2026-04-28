import re
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SanitizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 1024 * 1024):
        super().__init__(app)
        self._max_body_size = max_body_size
        self._sql_injection_pattern = re.compile(
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)",
            re.IGNORECASE
        )
        self._xss_pattern = re.compile(
            r"<script|javascript:|onerror=|onload=|onclick=|onmouseover=",
            re.IGNORECASE
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path.startswith("/api/"):
            return await call_next(request)

        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()

            if len(body) > self._max_body_size:
                logger.warning(
                    "Request body too large",
                    extra={
                        "path": request.url.path,
                        "body_size": len(body),
                        "max_size": self._max_body_size
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request body exceeds maximum size of {self._max_body_size} bytes"
                )

            body_str = body.decode("utf-8", errors="ignore")

            if self._sql_injection_pattern.search(body_str):
                logger.warning(
                    "Potential SQL injection detected",
                    extra={
                        "path": request.url.path,
                        "client_host": request.client.host if request.client else None
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )

            if self._xss_pattern.search(body_str):
                logger.warning(
                    "Potential XSS attack detected",
                    extra={
                        "path": request.url.path,
                        "client_host": request.client.host if request.client else None
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )

        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if isinstance(value, str):
                if self._sql_injection_pattern.search(value):
                    logger.warning(
                        "Potential SQL injection in query params",
                        extra={
                            "path": request.url.path,
                            "param": key,
                            "client_host": request.client.host if request.client else None
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )

                if self._xss_pattern.search(value):
                    logger.warning(
                        "Potential XSS in query params",
                        extra={
                            "path": request.url.path,
                            "param": key,
                            "client_host": request.client.host if request.client else None
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )

        return await call_next(request)
