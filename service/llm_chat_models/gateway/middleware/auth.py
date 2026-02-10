from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import AUTH_ENABLED, AUTH_SKIP_PATHS
from logic.persistence.postgres_store import PostgresAuthStore

class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.auth_store = PostgresAuthStore() if AUTH_ENABLED else None

    async def dispatch(self, request: Request, call_next):
        if not AUTH_ENABLED:
            return await call_next(request)
        path = request.url.path
        if any((path.startswith(p) for p in AUTH_SKIP_PATHS)):
            return await call_next(request)
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                api_key = auth_header.split(' ')[1]
        if not api_key:
            return JSONResponse(status_code=401, content={'detail': 'Missing API Key'})
        client_info = self.auth_store.validate_api_key(api_key)
        if not client_info:
            return JSONResponse(status_code=401, content={'detail': 'Invalid or inactive API Key'})
        request.state.client_id = client_info['client_id']
        request.state.client_name = client_info['client_name']
        request.state.scopes = client_info['scopes']
        return await call_next(request)