"""Main FastAPI application."""
from fastapi import FastAPI
from api.routes import health, collections, search
from core.config.settings import settings

app = FastAPI(
    title="Embedding Service",
    description="Vector embedding service with Qdrant",
    version="1.0.0"
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
