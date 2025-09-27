#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="embedding-service"

echo "🚀 Creating embedding service with vertical folder structure..."

# Create vertical folder structure
mkdir -p "$PROJECT_NAME"
mkdir -p "$PROJECT_NAME/data/qdrant"
mkdir -p "$PROJECT_NAME/api/routes"
mkdir -p "$PROJECT_NAME/api/middleware"
mkdir -p "$PROJECT_NAME/core/config"
mkdir -p "$PROJECT_NAME/core/models"
mkdir -p "$PROJECT_NAME/core/schemas"
mkdir -p "$PROJECT_NAME/services/embedding"
mkdir -p "$PROJECT_NAME/services/storage"
mkdir -p "$PROJECT_NAME/handlers"
mkdir -p "$PROJECT_NAME/utils"
mkdir -p "$PROJECT_NAME/tests/unit"
mkdir -p "$PROJECT_NAME/tests/integration"
mkdir -p "$PROJECT_NAME/scripts"

echo "📁 Folder structure created:"
echo "
$PROJECT_NAME/
├── data/qdrant/                 # Persistent Qdrant data
├── api/
│   ├── routes/                  # API route definitions
│   └── middleware/              # Custom middleware
├── core/
│   ├── config/                  # Configuration files
│   ├── models/                  # Data models
│   └── schemas/                 # Pydantic schemas
├── services/
│   ├── embedding/               # Embedding logic
│   └── storage/                 # Storage interfaces
├── handlers/                    # Request handlers
├── utils/                       # Utilities
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
└── scripts/                     # Deployment scripts
"

# === DOCKER COMPOSE ===
cat > "$PROJECT_NAME/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-db
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage:rw
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
    restart: unless-stopped

  embedding-api:
    build: .
    container_name: embedding-api
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - VECTOR_DIM=384
      - COLLECTION_NAME=embeddings
    depends_on:
      - qdrant
    volumes:
      - .:/app
    restart: unless-stopped

networks:
  default:
    driver: bridge
EOF

# === DOCKERFILE ===
cat > "$PROJECT_NAME/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# === REQUIREMENTS ===
cat > "$PROJECT_NAME/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
numpy==1.24.3
python-multipart==0.0.6
httpx==0.25.2
EOF

# === MAIN APP ===
cat > "$PROJECT_NAME/main.py" << 'EOF'
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
EOF

# === CORE CONFIG ===
cat > "$PROJECT_NAME/core/config/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/core/config/settings.py" << 'EOF'
"""Application settings."""
import os

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    VECTOR_DIM: int = int(os.getenv("VECTOR_DIM", "384"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "embeddings")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

settings = Settings()
EOF

# === CORE MODELS ===
cat > "$PROJECT_NAME/core/models/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/core/models/vector_point.py" << 'EOF'
"""Vector point data model."""
from typing import Dict, Any, List, Union
from dataclasses import dataclass

@dataclass
class VectorPoint:
    id: Union[str, int]
    vector: List[float]
    payload: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
EOF

# === CORE SCHEMAS ===
cat > "$PROJECT_NAME/core/schemas/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/core/schemas/requests.py" << 'EOF'
"""Request schemas."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class EmbedRequest(BaseModel):
    text: str
    collection: Optional[str] = None

class UpsertRequest(BaseModel):
    items: List[Dict[str, Any]]
    collection: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    collection: Optional[str] = None
    with_payload: bool = True

class CreateCollectionRequest(BaseModel):
    name: str
    vector_size: int = 384
    distance: str = "Cosine"
EOF

cat > "$PROJECT_NAME/core/schemas/responses.py" << 'EOF'
"""Response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "embedding-service"

class EmbedResponse(BaseModel):
    vector: List[float]
    dimension: int

class SearchResult(BaseModel):
    id: str
    score: float
    payload: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

class StatusResponse(BaseModel):
    success: bool
    message: str
EOF

# === SERVICES - EMBEDDING ===
cat > "$PROJECT_NAME/services/embedding/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/services/embedding/text_embedder.py" << 'EOF'
"""Text embedding service."""
import hashlib
from typing import List
import logging

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self, model_name: str = "demo", vector_dim: int = 384):
        self.model_name = model_name
        self.vector_dim = vector_dim
        self._load_model()
    
    def _load_model(self):
        """Load embedding model."""
        if self.model_name == "demo":
            logger.info("Using demo hash-based embedder")
        else:
            try:
                # Uncomment for production:
                # from sentence_transformers import SentenceTransformer
                # self.model = SentenceTransformer(self.model_name)
                pass
            except ImportError:
                logger.warning("sentence-transformers not available, using demo embedder")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.model_name == "demo":
            return self._hash_embed(text)
        else:
            # return self.model.encode(text).tolist()
            return self._hash_embed(text)
    
    def _hash_embed(self, text: str) -> List[float]:
        """Demo embedding using hash."""
        if not text:
            text = "empty"
        
        # Create deterministic hash
        hash_bytes = hashlib.sha256(text.lower().encode()).digest()
        
        # Convert to vector
        vector = []
        for i in range(self.vector_dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Normalize to [-1, 1]
            normalized = (byte_val - 127.5) / 127.5
            vector.append(float(normalized))
        
        return vector
EOF

# === SERVICES - STORAGE ===
cat > "$PROJECT_NAME/services/storage/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/services/storage/qdrant_client.py" << 'EOF'
"""Qdrant storage client."""
from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from core.models.vector_point import VectorPoint

logger = logging.getLogger(__name__)

class QdrantStorage:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.url = url
        logger.info(f"Connected to Qdrant at {url}")
    
    def create_collection(self, name: str, vector_size: int = 384, distance: str = "Cosine"):
        """Create a new collection."""
        distance_map = {
            "Cosine": Distance.COSINE,
            "Dot": Distance.DOT, 
            "Euclid": Distance.EUCLID
        }
        
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )
            logger.info(f"Created collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection {name}: {e}")
            return False
    
    def upsert_points(self, collection: str, points: List[VectorPoint]):
        """Insert or update points."""
        qdrant_points = [
            PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload
            ) for point in points
        ]
        
        try:
            self.client.upsert(
                collection_name=collection,
                points=qdrant_points,
                wait=True
            )
            logger.info(f"Upserted {len(points)} points to {collection}")
            return True
        except Exception as e:
            logger.error(f"Error upserting to {collection}: {e}")
            return False
    
    def search(
        self, 
        collection: str, 
        query_vector: List[float], 
        limit: int = 10,
        with_payload: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=limit,
                with_payload=with_payload
            )
            
            return [
                {
                    "id": str(point.id),
                    "score": float(point.score),
                    "payload": point.payload if with_payload else None
                }
                for point in results.points
            ]
        except Exception as e:
            logger.error(f"Error searching in {collection}: {e}")
            return []
EOF

# === HANDLERS ===
cat > "$PROJECT_NAME/handlers/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/handlers/embedding_handler.py" << 'EOF'
"""Embedding request handlers."""
from typing import List
from services.embedding.text_embedder import TextEmbedder
from services.storage.qdrant_client import QdrantStorage
from core.models.vector_point import VectorPoint
from core.config.settings import settings

class EmbeddingHandler:
    def __init__(self):
        self.embedder = TextEmbedder(
            model_name=settings.EMBEDDING_MODEL,
            vector_dim=settings.VECTOR_DIM
        )
        self.storage = QdrantStorage(settings.QDRANT_URL)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return self.embedder.embed(text)
    
    def store_embeddings(self, collection: str, items: List[dict]) -> bool:
        """Store text embeddings."""
        points = []
        for item in items:
            text = item.get("text", "")
            vector = self.embedder.embed(text)
            point = VectorPoint(
                id=item.get("id"),
                vector=vector,
                payload=item.get("payload", {})
            )
            points.append(point)
        
        return self.storage.upsert_points(collection, points)
    
    def search_similar(
        self, 
        collection: str, 
        query: str, 
        limit: int = 10,
        with_payload: bool = True
    ):
        """Search for similar texts."""
        query_vector = self.embedder.embed(query)
        return self.storage.search(collection, query_vector, limit, with_payload)
EOF

# === API ROUTES ===
cat > "$PROJECT_NAME/api/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/api/routes/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/api/routes/health.py" << 'EOF'
"""Health check routes."""
from fastapi import APIRouter
from core.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
EOF

cat > "$PROJECT_NAME/api/routes/collections.py" << 'EOF'
"""Collection management routes."""
from fastapi import APIRouter, HTTPException
from core.schemas.requests import CreateCollectionRequest, UpsertRequest
from core.schemas.responses import StatusResponse
from handlers.embedding_handler import EmbeddingHandler
from core.config.settings import settings

router = APIRouter(prefix="/collections", tags=["collections"])
handler = EmbeddingHandler()

@router.post("/create", response_model=StatusResponse)
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection."""
    success = handler.storage.create_collection(
        name=request.name,
        vector_size=request.vector_size,
        distance=request.distance
    )
    return StatusResponse(
        success=success,
        message=f"Collection {request.name} created" if success else "Failed to create collection"
    )

@router.post("/init", response_model=StatusResponse)
async def init_default_collection():
    """Initialize default collection."""
    if not handler.storage.collection_exists(settings.COLLECTION_NAME):
        success = handler.storage.create_collection(
            name=settings.COLLECTION_NAME,
            vector_size=settings.VECTOR_DIM
        )
        return StatusResponse(
            success=success,
            message=f"Initialized collection: {settings.COLLECTION_NAME}"
        )
    return StatusResponse(success=True, message="Collection already exists")

@router.post("/upsert", response_model=StatusResponse)
async def upsert_items(request: UpsertRequest):
    """Add items to collection."""
    collection = request.collection or settings.COLLECTION_NAME
    
    # Ensure collection exists
    if not handler.storage.collection_exists(collection):
        handler.storage.create_collection(collection, settings.VECTOR_DIM)
    
    success = handler.store_embeddings(collection, request.items)
    return StatusResponse(
        success=success,
        message=f"Upserted {len(request.items)} items" if success else "Failed to upsert items"
    )
EOF

cat > "$PROJECT_NAME/api/routes/search.py" << 'EOF'
"""Search routes."""
from fastapi import APIRouter
from core.schemas.requests import SearchRequest, EmbedRequest
from core.schemas.responses import SearchResponse, EmbedResponse
from handlers.embedding_handler import EmbeddingHandler
from core.config.settings import settings

router = APIRouter(tags=["search"])
handler = EmbeddingHandler()

@router.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """Generate embedding for text."""
    vector = handler.embed_text(request.text)
    return EmbedResponse(
        vector=vector,
        dimension=len(vector)
    )

@router.post("/search", response_model=SearchResponse)
async def search_similar(request: SearchRequest):
    """Search for similar items."""
    collection = request.collection or settings.COLLECTION_NAME
    
    results = handler.search_similar(
        collection=collection,
        query=request.query,
        limit=request.limit,
        with_payload=request.with_payload
    )
    
    return SearchResponse(
        results=results,
        total=len(results)
    )
EOF

# === MIDDLEWARE ===
cat > "$PROJECT_NAME/api/middleware/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/api/middleware/logging.py" << 'EOF'
"""Logging middleware."""
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response
EOF

# === UTILS ===
cat > "$PROJECT_NAME/utils/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/utils/helpers.py" << 'EOF'
"""Utility functions."""
import logging

def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def validate_vector_dim(vector, expected_dim):
    """Validate vector dimensions."""
    return len(vector) == expected_dim
EOF

# === TESTS ===
cat > "$PROJECT_NAME/tests/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/tests/unit/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/tests/unit/test_embeddings.py" << 'EOF'
"""Test embedding functionality."""
import pytest
from services.embedding.text_embedder import TextEmbedder

def test_text_embedder():
    embedder = TextEmbedder("demo", 384)
    vector = embedder.embed("test text")
    assert len(vector) == 384
    assert all(isinstance(v, float) for v in vector)

def test_consistent_embeddings():
    embedder = TextEmbedder("demo", 384)
    text = "consistent test"
    vec1 = embedder.embed(text)
    vec2 = embedder.embed(text)
    assert vec1 == vec2
EOF

cat > "$PROJECT_NAME/tests/integration/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/tests/integration/test_api.py" << 'EOF'
"""Test API endpoints."""
# Integration tests would go here
pass
EOF

# === SCRIPTS ===
cat > "$PROJECT_NAME/scripts/setup.py" << 'EOF'
"""Setup script for development."""
import subprocess
import sys

def install_dependencies():
    """Install Python dependencies."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def run_tests():
    """Run test suite."""
    subprocess.check_call([sys.executable, "-m", "pytest", "tests/"])

if __name__ == "__main__":
    print("Setting up embedding service...")
    install_dependencies()
    print("Setup complete!")
EOF

# === README ===
cat > "$PROJECT_NAME/README.md" << 'EOF'
# Embedding Service

Vector embedding microservice with Qdrant backend.

## 📁 Structure

```
embedding-service/
├── data/qdrant/                 # Persistent storage
├── api/routes/                  # FastAPI routes
├── core/                        # Core configuration & models
├── services/                    # Business logic
├── handlers/                    # Request processing
├── utils/                       # Helper functions
└── tests/                       # Test suites
```

## 🚀 Quick Start

```bash
# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# Initialize collection
curl -X POST http://localhost:8000/api/v1/collections/init

# Add data
curl -X POST http://localhost:8000/api/v1/collections/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "1", "text": "Machine learning is fascinating", "payload": {"category": "tech"}},
      {"id": "2", "text": "Deep learning models are powerful", "payload": {"category": "ai"}}
    ]
  }'

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "limit": 5}'
```

## 🔧 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# Run tests
pytest tests/
```

## 📊 API Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/collections/init` - Initialize default collection
- `POST /api/v1/collections/create` - Create new collection
- `POST /api/v1/collections/upsert` - Add/update items
- `POST /api/v1/embed` - Generate text embedding
- `POST /api/v1/search` - Search similar items

## 🌐 Access

- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard
EOF

# === .gitignore ===
cat > "$PROJECT_NAME/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
data/qdrant/*
!data/qdrant/.gitkeep
logs/
*.log
EOF

# Create empty .gitkeep for qdrant data directory
touch "$PROJECT_NAME/data/qdrant/.gitkeep"

echo "✅ Embedding service created successfully!"
echo ""
echo "📋 Quick Commands:"
echo "cd $PROJECT_NAME"
echo "docker-compose up -d              # Start services"
echo "curl localhost:8000/api/v1/health # Health check"
echo ""
echo "🌐 Access URLs:"
echo "- API: http://localhost:8000/docs"
echo "- Qdrant: http://localhost:6333/dashboard"