import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from .config import settings
from .cf_client import CloudflareAIClient
from .models import GenerateRequest, GenerateResponse, HealthResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global client instance
cf_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global cf_client
    
    # Startup
    logger.info("Starting Cloudflare AI Proxy...")
    cf_client = CloudflareAIClient(
        account_id=settings.cf_account_id,
        api_token=settings.cf_api_token,
        timeout=settings.http_timeout_seconds
    )
    logger.info(f"Using model: {settings.model_id}")
    yield
    
    # Shutdown
    logger.info("Shutting down Cloudflare AI Proxy...")

# FastAPI app with lifespan management
app = FastAPI(
    title="Cloudflare AI Proxy",
    description="Fast proxy API for Cloudflare Workers AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Cloudflare AI Proxy",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "/v1/generate"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test Cloudflare API connectivity
        cf_healthy = await cf_client.health_check()
        
        return HealthResponse(
            status="healthy" if cf_healthy else "degraded",
            model_id=settings.model_id,
            version="1.0.0",
            cloudflare_api_healthy=cf_healthy
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            model_id=settings.model_id,
            version="1.0.0",
            cloudflare_api_healthy=False
        )

@app.post("/v1/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text using Cloudflare Workers AI"""
    try:
        # Prepare inference parameters
        inference_params = dict(settings.inference_params)
        
        # Override with request parameters if provided
        if request.max_tokens is not None:
            inference_params["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            inference_params["temperature"] = request.temperature
        if request.top_p is not None:
            inference_params["top_p"] = request.top_p
        
        # Call Cloudflare AI
        logger.info(f"Generating text for prompt length: {len(request.prompt)}")
        result = await cf_client.generate_text(
            model_id=settings.model_id,
            prompt=request.prompt,
            **inference_params
        )
        
        # Extract response text
        response_data = result.get("result", {})
        generated_text = response_data.get("response", "")
        
        if not generated_text:
            logger.warning("Empty response from Cloudflare AI")
            raise HTTPException(status_code=502, detail="Empty response from AI model")
        
        return GenerateResponse(
            model_id=settings.model_id,
            response=generated_text,
            prompt=request.prompt,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Text generation failed: {str(e)}"
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
