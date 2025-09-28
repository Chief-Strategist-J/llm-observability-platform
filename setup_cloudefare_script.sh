#!/bin/bash
set -e

echo "Creating Cloudflare AI Proxy with vertical folder structure..."

# Create main project directory and subdirectories
mkdir -p cloudflare-ai-proxy/app
mkdir -p cloudflare-ai-proxy/configs

cd cloudflare-ai-proxy

# ---------------- requirements.txt ----------------
cat > requirements.txt <<'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
pydantic>=2.5.0
pyyaml==6.0.1
python-dotenv==1.0.0
EOF

# ---------------- .env.example ----------------
cat > .env.example <<'EOF'
# Cloudflare Workers AI credentials (REQUIRED)
CF_ACCOUNT_ID=your_cloudflare_account_id_here
CF_API_TOKEN=your_cloudflare_api_token_here

# Optional: override model without editing configs/model.yaml
# MODEL_ID=@cf/meta/llama-3.2-1b-instruct

# Server configuration
HOST=0.0.0.0
PORT=8080

# HTTP client settings
HTTP_TIMEOUT_SECONDS=30

# Environment
ENV=production
EOF

# ---------------- configs/model.yaml ----------------
cat > configs/model.yaml <<'EOF'
# Default model (small, fast, cheap)
model_id: "@cf/meta/llama-3.2-1b-instruct"

# Inference parameters (optimized for speed and cost)
inference:
  max_tokens: 256
  temperature: 0.7
  top_p: 0.95
  
# Alternative models you can switch to:
# model_id: "@cf/mistral/mistral-7b-instruct-v0.1"
# model_id: "@cf/meta/llama-3.1-8b-instruct"
# model_id: "@cf/microsoft/phi-2"
EOF

# ---------------- app/__init__.py ----------------
cat > app/__init__.py <<'EOF'
"""Cloudflare AI Proxy - FastAPI microservice"""
__version__ = "1.0.0"
EOF

# ---------------- app/config.py ----------------
cat > app/config.py <<'EOF'
import os
import yaml
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path

# Get project root directory
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "configs" / "model.yaml"

@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment and config files"""
    cf_account_id: str
    cf_api_token: str
    model_id: str
    inference_params: Dict[str, Any]
    host: str
    port: int
    http_timeout_seconds: float
    environment: str

def load_model_config() -> Dict[str, Any]:
    """Load model configuration from YAML file"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Warning: Config file {CONFIG_PATH} not found, using defaults")
        return {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def load_settings() -> Settings:
    """Load all application settings"""
    config = load_model_config()
    
    # Required Cloudflare credentials
    cf_account_id = os.getenv("CF_ACCOUNT_ID", "").strip()
    cf_api_token = os.getenv("CF_API_TOKEN", "").strip()
    
    if not cf_account_id:
        raise ValueError("CF_ACCOUNT_ID environment variable is required")
    if not cf_api_token:
        raise ValueError("CF_API_TOKEN environment variable is required")
    
    # Model configuration (ENV can override YAML)
    model_id = os.getenv("MODEL_ID") or config.get("model_id", "@cf/meta/llama-3.2-1b-instruct")
    inference_params = config.get("inference", {})
    
    return Settings(
        cf_account_id=cf_account_id,
        cf_api_token=cf_api_token,
        model_id=model_id,
        inference_params=inference_params,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        environment=os.getenv("ENV", "production")
    )

# Global settings instance
settings = load_settings()
EOF

# ---------------- app/cf_client.py ----------------
cat > app/cf_client.py <<'EOF'
import json
import httpx
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CloudflareAIClient:
    """Async client for Cloudflare Workers AI API"""
    
    def __init__(self, account_id: str, api_token: str, timeout: float = 30):
        self.account_id = account_id
        self.api_token = api_token
        self.timeout = timeout
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"
        
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "User-Agent": "CloudflareAI-Proxy/1.0"
        }
    
    async def generate_text(
        self,
        model_id: str,
        prompt: str,
        **inference_params: Any
    ) -> Dict[str, Any]:
        """Generate text using Cloudflare Workers AI"""
        url = f"{self.base_url}/{model_id}"
        
        payload = {
            "prompt": prompt,
            **inference_params
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling Cloudflare AI: {model_id}")
                response = await client.post(
                    url,
                    headers=self.headers,
                    content=json.dumps(payload)
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling Cloudflare AI after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """Simple health check by making a minimal API call"""
        try:
            await self.generate_text(
                model_id="@cf/meta/llama-3.2-1b-instruct",
                prompt="Hi",
                max_tokens=1
            )
            return True
        except Exception:
            return False
EOF

# ---------------- app/models.py ----------------
cat > app/models.py <<'EOF'
from pydantic import BaseModel, Field
from typing import Optional

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Input prompt for the AI model", min_length=1)
    
    # Optional inference parameter overrides
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate", gt=0, le=2048)
    temperature: Optional[float] = Field(None, description="Sampling temperature", ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, description="Top-p sampling parameter", ge=0.0, le=1.0)

class GenerateResponse(BaseModel):
    """Response model for text generation"""
    model_id: str = Field(..., description="Model used for generation")
    response: str = Field(..., description="Generated text response")
    prompt: str = Field(..., description="Original prompt")
    success: bool = Field(default=True, description="Whether generation was successful")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_id: str
    version: str
    cloudflare_api_healthy: bool
EOF

# ---------------- app/main.py ----------------
cat > app/main.py <<'EOF'
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
EOF

# ---------------- Dockerfile ----------------
cat > Dockerfile <<'EOF'
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY configs/ ./configs/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF

# ---------------- docker-compose.yml ----------------
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  cloudflare-ai-proxy:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=production
    env_file:
      - .env
    volumes:
      # Mount config for hot-swapping models
      - ./configs/model.yaml:/app/configs/model.yaml:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ai-proxy-network

networks:
  ai-proxy-network:
    driver: bridge
EOF

# ---------------- docker-compose.dev.yml (for development) ----------------
cat > docker-compose.dev.yml <<'EOF'
version: '3.8'

services:
  cloudflare-ai-proxy:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=development
    env_file:
      - .env
    volumes:
      # Mount entire app for hot reload in development
      - ./app:/app/app:ro
      - ./configs:/app/configs:ro
    restart: unless-stopped
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
    networks:
      - ai-proxy-network

networks:
  ai-proxy-network:
    driver: bridge
EOF

# ---------------- Makefile ----------------
cat > Makefile <<'EOF'
.PHONY: help install dev build up down logs test clean

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies locally"
	@echo "  dev        - Run development server"
	@echo "  build      - Build Docker image"
	@echo "  up         - Start Docker containers"
	@echo "  up-dev     - Start Docker containers in dev mode"
	@echo "  down       - Stop Docker containers"
	@echo "  logs       - View Docker logs"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up Docker resources"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

build:
	docker build -t cloudflare-ai-proxy:latest .

up:
	docker-compose up -d

up-dev:
	docker-compose -f docker-compose.dev.yml up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Testing API endpoints..."
	@echo "Health check:"
	curl -s http://localhost:8080/health | python -m json.tool || echo "Service not running"
	@echo "\nGenerate test:"
	curl -s -X POST http://localhost:8080/v1/generate \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Hello, how are you?", "max_tokens": 50}' | python -m json.tool || echo "Service not running"

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
EOF

# ---------------- .dockerignore ----------------
cat > .dockerignore <<'EOF'
.git
.gitignore
README.md
.env
.env.example
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
.venv
venv/
.DS_Store
EOF

# ---------------- .gitignore ----------------
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.production

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore
EOF

# ---------------- README.md ----------------
cat > README.md <<'EOF'
# Cloudflare AI Proxy

A fast, minimal FastAPI microservice that provides a clean REST API for Cloudflare Workers AI.

## Features

- 🚀 **Fast**: Optimized for low latency with async HTTP client
- 💰 **Cost-effective**: Uses Cloudflare's cheap AI models
- 🔧 **Hot-swappable**: Change models without rebuilding containers
- 🐳 **Docker ready**: Production-ready containerization
- 📊 **Monitoring**: Health checks and request timing
- 🛡️ **Secure**: Non-root containers with proper error handling

## Quick Start

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Cloudflare credentials
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8080/health

   # Generate text
   curl -X POST http://localhost:8080/v1/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}'
   ```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check with Cloudflare API status
- `POST /v1/generate` - Generate text

## Configuration

Edit `configs/model.yaml` to change models without rebuilding:

```yaml
model_id: "@cf/meta/llama-3.2-1b-instruct"
inference:
  max_tokens: 256
  temperature: 0.7
  top_p: 0.95
```

## Development

```bash
# Local development
make dev

# Development with Docker (hot reload)
make up-dev
```

## Available Models

- `@cf/meta/llama-3.2-1b-instruct` (default - fastest, cheapest)
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@cf/microsoft/phi-2`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CF_ACCOUNT_ID` | Cloudflare Account ID | ✅ |
| `CF_API_TOKEN` | Cloudflare API Token | ✅ |
| `MODEL_ID` | Override model from config | ❌ |
| `HOST` | Server host | ❌ |
| `PORT` | Server port | ❌ |

## Pricing

Cloudflare Workers AI pricing (as of 2024):
- Free tier: 10,000 requests/day
- Pay-as-you-go: ~$0.001-0.01 per request (model dependent)

## License

MIT License
EOF

echo "✅ Cloudflare AI Proxy created successfully!"
echo ""
echo "📁 Project structure:"
echo "cloudflare-ai-proxy/"
echo "├── app/"
echo "│   ├── __init__.py"
echo "│   ├── main.py          # FastAPI app with endpoints"
echo "│   ├── cf_client.py     # Cloudflare AI client"
echo "│   ├── config.py        # Configuration management"
echo "│   └── models.py        # Pydantic models"
echo "├── configs/"
echo "│   └── model.yaml       # Model configuration (hot-swappable)"
echo "├── requirements.txt"
echo "├── Dockerfile"
echo "├── docker-compose.yml"
echo "├── docker-compose.dev.yml"
echo "├── Makefile"
echo "└── README.md"
echo ""
echo "🚀 Next steps:"
echo "1. Copy environment file:     cp .env.example .env"
echo "2. Edit .env with your Cloudflare Account ID and API Token"
echo "3. Start the service:         docker compose up -d"
echo "4. Test the API:              make test"
echo ""
echo "📚 Get Cloudflare credentials at: https://dash.cloudflare.com/profile/api-tokens"
echo ""