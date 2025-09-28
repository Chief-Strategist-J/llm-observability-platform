"""Main FastAPI application."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import health, collections, search
from core.config.settings import settings
from utils.helpers import setup_logging
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Embedding Service",
    description="High-performance vector embedding service with Qdrant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Embedding Service starting up...")
    logger.info(f"Qdrant URL: {settings.QDRANT_URL}")
    logger.info(f"Vector dimensions: {settings.VECTOR_DIM}")
    logger.info(f"Default collection: {settings.COLLECTION_NAME}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Embedding Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
