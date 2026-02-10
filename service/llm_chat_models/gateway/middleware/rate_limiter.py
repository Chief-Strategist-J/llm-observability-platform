from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import AUTH_ENABLED, AUTH_SKIP_PATHS, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from logic.persistence.postgres_store import PostgresAuthStore

class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.store = PostgresAuthStore() if AUTH_ENABLED else None

    async def dispatch(self, request: Request, call_next):
        if not AUTH_ENABLED or not self.store:
            return await call_next(request)
        path = request.url.path
        if any((path.startswith(p) for p in AUTH_SKIP_PATHS)):
            return await call_next(request)
        client_id = getattr(request.state, 'client_id', None)
        if not client_id:
            return await call_next(request)
        limit_info = self.store.check_rate_limit(client_id, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
        if not limit_info['allowed']:
            return JSONResponse(status_code=429, content={'detail': 'Rate limit exceeded', 'retry_after': limit_info['retry_after']}, headers={'Retry-After': str(int(limit_info['retry_after']))})
        response = await call_next(request)
        response.headers['X-RateLimit-Limit'] = str(limit_info['max_requests'])
        response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(int(limit_info['retry_after']))
        return response