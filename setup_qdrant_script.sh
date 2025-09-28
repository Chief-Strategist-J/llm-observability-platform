#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="embedding-service"

echo "🚀 Creating optimized embedding service for local development..."

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

echo "📁 Folder structure created successfully!"

# === DOCKER COMPOSE (Optimized for local dev) ===
cat > "$PROJECT_NAME/docker-compose.yml" << 'EOF'
services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant-db
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage:rw
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s

  embedding-api:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: embedding-api
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - VECTOR_DIM=384
      - COLLECTION_NAME=embeddings
      - EMBEDDING_MODEL=demo
      - LOG_LEVEL=INFO
    depends_on:
      qdrant:
        condition: service_healthy
    volumes:
      - .:/app:rw
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

networks:
  default:
    driver: bridge
EOF

# === DOCKERFILE (Optimized for development) ===
cat > "$PROJECT_NAME/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# === .dockerignore ===
cat > "$PROJECT_NAME/.dockerignore" << 'EOF'
# Git
.git
.gitignore

# Docker
Dockerfile
.dockerignore
docker-compose*.yml

# Development
.venv/
venv/
env/
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
Thumbs.db
ehthumbs.db

# Logs
*.log
logs/

# Documentation
README.md
docs/

# Tests (exclude from production image)
tests/
.coverage
.tox/
htmlcov/

# Data (will be mounted as volume)
data/
EOF

# === CPU-OPTIMIZED REQUIREMENTS ===
cat > "$PROJECT_NAME/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
qdrant-client==1.7.0
numpy==1.24.3
python-multipart==0.0.6
httpx==0.25.2
EOF

# === PRODUCTION REQUIREMENTS (for later scaling) ===
cat > "$PROJECT_NAME/requirements-production.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
torch==2.1.0+cpu
torchvision==0.16.0+cpu
torchaudio==2.1.0+cpu
--extra-index-url https://download.pytorch.org/whl/cpu
transformers==4.35.0
numpy==1.24.3
python-multipart==0.0.6
httpx==0.25.2
scikit-learn==1.3.0
EOF

# === MAIN APP ===
cat > "$PROJECT_NAME/main.py" << 'EOF'
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
EOF

# === CORE CONFIG ===
cat > "$PROJECT_NAME/core/config/__init__.py" << 'EOF'
"""Core configuration package."""
EOF

cat > "$PROJECT_NAME/core/config/settings.py" << 'EOF'
"""Application settings with validation."""
import os
from typing import Optional

class Settings:
    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # Vector Configuration
    VECTOR_DIM: int = int(os.getenv("VECTOR_DIM", "384"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "embeddings")
    DISTANCE_METRIC: str = os.getenv("DISTANCE_METRIC", "Cosine")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "demo")
    
    # API Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    def validate(self):
        """Validate configuration."""
        assert self.VECTOR_DIM > 0, "VECTOR_DIM must be positive"
        assert self.DISTANCE_METRIC in ["Cosine", "Dot", "Euclid"], "Invalid distance metric"
        assert self.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"], "Invalid log level"

settings = Settings()
settings.validate()
EOF

# === CORE MODELS ===
cat > "$PROJECT_NAME/core/models/__init__.py" << 'EOF'
"""Core models package."""
EOF

cat > "$PROJECT_NAME/core/models/vector_point.py" << 'EOF'
"""Vector point data model."""
from typing import Dict, Any, List, Union
from dataclasses import dataclass, field

@dataclass
class VectorPoint:
    """Represents a vector point with metadata."""
    id: Union[str, int]
    vector: List[float]
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate vector point after initialization."""
        if not isinstance(self.id, (str, int)):
            raise ValueError("ID must be string or integer")
        if not isinstance(self.vector, list) or not all(isinstance(x, (int, float)) for x in self.vector):
            raise ValueError("Vector must be list of numbers")
        if not isinstance(self.payload, dict):
            raise ValueError("Payload must be dictionary")
EOF

# === CORE SCHEMAS ===
cat > "$PROJECT_NAME/core/schemas/__init__.py" << 'EOF'
"""Core schemas package."""
EOF

cat > "$PROJECT_NAME/core/schemas/requests.py" << 'EOF'
"""Request schemas with validation."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to embed")
    collection: Optional[str] = Field(None, description="Collection name")

class UpsertRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., min_items=1, description="Items to upsert")
    collection: Optional[str] = Field(None, description="Collection name")
    
    @validator('items')
    def validate_items(cls, v):
        for item in v:
            if 'id' not in item:
                raise ValueError("Each item must have an 'id' field")
            if 'text' not in item and 'vector' not in item:
                raise ValueError("Each item must have either 'text' or 'vector' field")
        return v

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Number of results")
    collection: Optional[str] = Field(None, description="Collection name")
    with_payload: bool = Field(True, description="Include payload in results")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum score threshold")

class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Collection name")
    vector_size: int = Field(384, ge=1, le=4096, description="Vector dimensions")
    distance: str = Field("Cosine", description="Distance metric")
    
    @validator('distance')
    def validate_distance(cls, v):
        if v not in ["Cosine", "Dot", "Euclid"]:
            raise ValueError("Distance must be one of: Cosine, Dot, Euclid")
        return v
EOF

cat > "$PROJECT_NAME/core/schemas/responses.py" << 'EOF'
"""Response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "embedding-service"
    version: str = "1.0.0"

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
    query_time_ms: Optional[float] = None

class StatusResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    code: int = 500
EOF

# === SERVICES - EMBEDDING ===
cat > "$PROJECT_NAME/services/embedding/__init__.py" << 'EOF'
"""Embedding services package."""
EOF

cat > "$PROJECT_NAME/services/embedding/text_embedder.py" << 'EOF'
"""Text embedding service with multiple model support."""
import hashlib
import time
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TextEmbedder:
    """Text embedding service supporting multiple models."""
    
    def __init__(self, model_name: str = "demo", vector_dim: int = 384):
        self.model_name = model_name
        self.vector_dim = vector_dim
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model based on configuration."""
        if self.model_name == "demo":
            logger.info("Using demo hash-based embedder")
        else:
            try:
                # For production scaling - uncomment when needed:
                # from sentence_transformers import SentenceTransformer
                # self.model = SentenceTransformer(self.model_name)
                # logger.info(f"Loaded model: {self.model_name}")
                logger.info(f"Model {self.model_name} not available, using demo embedder")
                self.model_name = "demo"  # Fallback
            except ImportError:
                logger.warning("sentence-transformers not available, using demo embedder")
                self.model_name = "demo"
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not text or not text.strip():
            text = "empty_text"
        
        if self.model_name == "demo":
            return self._hash_embed(text)
        else:
            # For production models:
            # return self.model.encode(text, convert_to_tensor=False).tolist()
            return self._hash_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.model_name == "demo":
            return [self._hash_embed(text) for text in texts]
        else:
            # For production models:
            # return self.model.encode(texts, convert_to_tensor=False).tolist()
            return [self._hash_embed(text) for text in texts]
    
    def _hash_embed(self, text: str) -> List[float]:
        """Generate deterministic demo embedding using SHA256."""
        # Normalize text for consistency
        text = text.lower().strip()
        
        # Create deterministic hash
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        
        # Convert to vector with good distribution
        vector = []
        for i in range(self.vector_dim):
            # Use multiple bytes for better distribution
            byte_idx1 = i % len(hash_bytes)
            byte_idx2 = (i + 1) % len(hash_bytes)
            
            byte_val = (hash_bytes[byte_idx1] + hash_bytes[byte_idx2]) / 2
            # Normalize to [-1, 1] for cosine similarity
            normalized = (byte_val - 127.5) / 127.5
            vector.append(float(normalized))
        
        return vector
EOF

# === SERVICES - STORAGE ===
cat > "$PROJECT_NAME/services/storage/__init__.py" << 'EOF'
"""Storage services package."""
EOF

cat > "$PROJECT_NAME/services/storage/qdrant_client.py" << 'EOF'
"""Enhanced Qdrant storage client with full API support."""
from typing import List, Dict, Any, Optional, Union
import logging
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException
from core.models.vector_point import VectorPoint

logger = logging.getLogger(__name__)

class QdrantStorage:
    """Enhanced Qdrant storage client supporting all major operations."""
    
    def __init__(self, url: str):
        self.url = url
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Qdrant with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client = QdrantClient(url=self.url, timeout=30)
                # Test connection
                self.client.get_collections()
                logger.info(f"Connected to Qdrant at {self.url}")
                return
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Qdrant after {max_retries} attempts")
                time.sleep(2)
    
    def _get_distance_enum(self, distance: str) -> Distance:
        """Convert string to Qdrant Distance enum."""
        distance_map = {
            "Cosine": Distance.COSINE,
            "Dot": Distance.DOT, 
            "Euclid": Distance.EUCLID,
            "Manhattan": Distance.MANHATTAN
        }
        return distance_map.get(distance.upper().title(), Distance.COSINE)
    
    def create_collection(self, name: str, vector_size: int = 384, distance: str = "Cosine") -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=self._get_distance_enum(distance)
                )
            )
            logger.info(f"Created collection: {name} (size={vector_size}, distance={distance})")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Collection {name} already exists")
                return True
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
            return False
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [
                {
                    "name": c.name,
                    "vectors_count": getattr(c, 'vectors_count', 0),
                    "segments_count": getattr(c, 'segments_count', 0)
                }
                for c in collections.collections
            ]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection {name}: {e}")
            return False
    
    def get_collection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed collection information."""
        try:
            info = self.client.get_collection(collection_name=name)
            return {
                "name": name,
                "vectors_count": info.vectors_count,
                "segments_count": info.segments_count,
                "disk_data_size": info.disk_data_size,
                "ram_data_size": info.ram_data_size,
                "config": {
                    "distance": info.config.params.vectors.distance.value,
                    "vector_size": info.config.params.vectors.size
                }
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {name}: {e}")
            return None
    
    def upsert_points(self, collection: str, points: List[VectorPoint]) -> bool:
        """Insert or update points."""
        try:
            qdrant_points = [
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload
                ) for point in points
            ]
            
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
        with_payload: bool = True,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional filtering."""
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                # Simple filter support - extend as needed
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                query_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=with_payload,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            return [
                {
                    "id": str(point.id),
                    "score": float(point.score),
                    "payload": point.payload if with_payload else None
                }
                for point in results
            ]
        except Exception as e:
            logger.error(f"Error searching in {collection}: {e}")
            return []
    
    def get_point(self, collection: str, point_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get a specific point by ID."""
        try:
            point = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )
            if point:
                p = point[0]
                return {
                    "id": str(p.id),
                    "vector": p.vector,
                    "payload": p.payload
                }
            return None
        except Exception as e:
            logger.error(f"Error getting point {point_id} from {collection}: {e}")
            return None
    
    def delete_points(self, collection: str, point_ids: List[Union[str, int]]) -> bool:
        """Delete specific points."""
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=point_ids,
                wait=True
            )
            logger.info(f"Deleted {len(point_ids)} points from {collection}")
            return True
        except Exception as e:
            logger.error(f"Error deleting points from {collection}: {e}")
            return False
    
    def count_points(self, collection: str) -> int:
        """Count total points in collection."""
        try:
            info = self.client.get_collection(collection_name=collection)
            return info.vectors_count
        except Exception as e:
            logger.error(f"Error counting points in {collection}: {e}")
            return 0
EOF

# === HANDLERS ===
cat > "$PROJECT_NAME/handlers/__init__.py" << 'EOF'
"""Request handlers package."""
EOF

cat > "$PROJECT_NAME/handlers/embedding_handler.py" << 'EOF'
"""Enhanced embedding request handler."""
from typing import List, Dict, Any, Optional
import time
import logging
from services.embedding.text_embedder import TextEmbedder
from services.storage.qdrant_client import QdrantStorage
from core.models.vector_point import VectorPoint
from core.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingHandler:
    """Enhanced embedding handler with comprehensive operations."""
    
    def __init__(self):
        self.embedder = TextEmbedder(
            model_name=settings.EMBEDDING_MODEL,
            vector_dim=settings.VECTOR_DIM
        )
        self.storage = QdrantStorage(settings.QDRANT_URL)
        logger.info("EmbeddingHandler initialized")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        start_time = time.time()
        vector = self.embedder.embed(text)
        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Generated embedding in {elapsed:.2f}ms")
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        start_time = time.time()
        vectors = self.embedder.embed_batch(texts)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Generated {len(vectors)} embeddings in {elapsed:.2f}ms")
        return vectors
    
    def store_embeddings(self, collection: str, items: List[dict]) -> Dict[str, Any]:
        """Store text embeddings with detailed response."""
        start_time = time.time()
        
        try:
            # Ensure collection exists
            if not self.storage.collection_exists(collection):
                self.storage.create_collection(collection, settings.VECTOR_DIM, settings.DISTANCE_METRIC)
            
            # Process items
            points = []
            for item in items:
                try:
                    if "vector" in item:
                        vector = item["vector"]
                        if len(vector) != settings.VECTOR_DIM:
                            raise ValueError(f"Vector dimension mismatch: expected {settings.VECTOR_DIM}, got {len(vector)}")
                    else:
                        text = item.get("text", "")
                        vector = self.embedder.embed(text)
                    
                    point = VectorPoint(
                        id=item.get("id"),
                        vector=vector,
                        payload=item.get("payload", {})
                    )
                    points.append(point)
                except Exception as e:
                    logger.error(f"Error processing item {item.get('id', 'unknown')}: {e}")
                    continue
            
            if not points:
                return {"success": False, "message": "No valid points to store"}
            
            # Store points
            success = self.storage.upsert_points(collection, points)
            elapsed = (time.time() - start_time) * 1000
            
            return {
                "success": success,
                "message": f"Processed {len(points)} items in {elapsed:.2f}ms",
                "processed": len(points),
                "failed": len(items) - len(points)
            }
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return {"success": False, "message": str(e)}
    
    def search_similar(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        with_payload: bool = True,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar texts with comprehensive response."""
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_vector = self.embedder.embed(query)
            embed_time = (time.time() - start_time) * 1000
            
            # Perform search
            search_start = time.time()
            results = self.storage.search(
                collection=collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=with_payload,
                score_threshold=score_threshold,
                filter_conditions=filters
            )
            search_time = (time.time() - search_start) * 1000
            total_time = (time.time() - start_time) * 1000
            
            return {
                "results": results,
                "total": len(results),
                "query_time_ms": total_time,
                "embedding_time_ms": embed_time,
                "search_time_ms": search_time,
                "query": query,
                "collection": collection
            }
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {
                "results": [],
                "total": 0,
                "error": str(e)
            }
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.storage.get_collection_info(collection)
            if info:
                return {
                    "exists": True,
                    "name": info["name"],
                    "vectors_count": info["vectors_count"],
                    "segments_count": info["segments_count"],
                    "disk_size_bytes": info["disk_data_size"],
                    "ram_size_bytes": info["ram_data_size"],
                    "vector_config": info["config"]
                }
            else:
                return {"exists": False, "name": collection}
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"exists": False, "error": str(e)}
EOF