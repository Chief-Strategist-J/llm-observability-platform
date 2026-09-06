import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from budget_provisioner.shared.di.container import Container
from budget_provisioner.infra.tracing.tracer import init_tracer
from budget_provisioner.api.rest.v1.router import router as v1_router

def create_app(container: Container | None = None) -> FastAPI:
    init_tracer()
    
    app = FastAPI(
        title="Budget Provisioner API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    app.state.container = container or Container()
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request.app.state.container.metrics_adapter.record_request(
            request.method, request.url.path, exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request.app.state.container.metrics_adapter.record_request(
            request.method, request.url.path, status.HTTP_400_BAD_REQUEST
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request.app.state.container.metrics_adapter.record_request(
            request.method, request.url.path, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        response = await call_next(request)
        app.state.container.metrics_adapter.record_request(
            request.method, request.url.path, response.status_code
        )
        return response

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "budget-provisioner"}

    app.include_router(v1_router)
    
    return app

app = create_app()

if __name__ == "__main__":
    config = app.state.container.config
    uvicorn.run(
        "budget_provisioner.api.main:app",
        host=config.host,
        port=config.port,
        reload=True
    )
