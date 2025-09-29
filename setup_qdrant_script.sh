#!/usr/bin/env bash
# Creates a complete RAG service (FastAPI + Qdrant) and starts it with Docker.
# Usage: bash setup_rag_service.sh
set -euo pipefail

PROJECT="rag-service"

echo "==> Rebuilding $PROJECT ..."
rm -rf "$PROJECT"
mkdir -p "$PROJECT"/{adapters/vector_store,adapters/document_parser,adapters/embedding_model,core/domain,core/ports,core/usecases,api,logs}

# -------------------- docker-compose.yml --------------------
cat > "$PROJECT/docker-compose.yml" <<'EOF'
services:
  qdrant:
    image: qdrant/qdrant:v1.6.1
    container_name: qdrant-db
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  api:
    build: .
    container_name: rag-api
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant-db:6333
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G

volumes:
  qdrant_data:
EOF

# -------------------- Dockerfile --------------------
cat > "$PROJECT/Dockerfile" <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --no-deps sentence-transformers==2.2.2 && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs && chmod 755 logs

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# -------------------- requirements.txt --------------------
cat > "$PROJECT/requirements.txt" <<'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.3
python-multipart==0.0.6
qdrant-client==1.6.4
pymupdf==1.23.14
transformers==4.30.0
tokenizers==0.13.3
huggingface-hub==0.16.4
safetensors==0.3.1
numpy==1.24.3
scikit-learn==1.3.0
scipy==1.11.1
tqdm==4.65.0
filelock==3.12.2
regex==2023.6.3
nltk==3.8.1
pillow==10.0.0
EOF

# -------------------- core/domain --------------------
: > "$PROJECT/core/__init__.py"
: > "$PROJECT/core/domain/__init__.py"

cat > "$PROJECT/core/domain/models.py" <<'EOF'
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Chunk:
    id: str
    text: str
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    chunk: Chunk
    score: float

@dataclass
class QueryRequest:
    query: str
    limit: int = 5
EOF

# -------------------- core/ports --------------------
: > "$PROJECT/core/ports/__init__.py"

cat > "$PROJECT/core/ports/vector_store.py" <<'EOF'
from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Chunk, SearchResult

class VectorStorePort(ABC):
    @abstractmethod
    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, embedding: List[float], limit: int) -> List[SearchResult]:
        raise NotImplementedError
EOF

cat > "$PROJECT/core/ports/document_parser.py" <<'EOF'
from abc import ABC, abstractmethod
from typing import AsyncIterator

class DocumentParserPort(ABC):
    @abstractmethod
    async def parse(self, file_bytes: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    async def chunk(self, text: str) -> AsyncIterator[str]:
        raise NotImplementedError
EOF

cat > "$PROJECT/core/ports/embedding_model.py" <<'EOF'
from abc import ABC, abstractmethod
from typing import List

class EmbeddingModelPort(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError
EOF

# -------------------- core/usecases --------------------
: > "$PROJECT/core/usecases/__init__.py"

cat > "$PROJECT/core/usecases/ingest.py" <<'EOF'
from typing import List
import logging
from uuid import uuid4
from core.domain.models import Chunk
from core.ports.document_parser import DocumentParserPort
from core.ports.embedding_model import EmbeddingModelPort
from core.ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)

async def ingest_document(
    file_bytes: bytes,
    filename: str,
    parser: DocumentParserPort,
    embedder: EmbeddingModelPort,
    vector_store: VectorStorePort
) -> dict:
    logger.info(f"Ingesting: {filename}")

    text = await parser.parse(file_bytes)
    logger.info(f"Extracted {len(text)} chars")

    chunks: List[Chunk] = []
    texts: List[str] = []

    async for chunk_text in parser.chunk(text):
        idx = len(chunks)
        chunks.append(Chunk(
            id=str(uuid4()),
            text=chunk_text,
            metadata={"filename": filename, "chunk_index": idx}
        ))
        texts.append(chunk_text)

    logger.info(f"Created {len(chunks)} chunks")

    embeddings = await embedder.embed_batch(texts)
    await vector_store.upsert(chunks, embeddings)

    logger.info(f"Stored {len(chunks)} chunks")
    return {"chunks": len(chunks), "filename": filename}
EOF

cat > "$PROJECT/core/usecases/search.py" <<'EOF'
import logging
from core.domain.models import QueryRequest
from core.ports.embedding_model import EmbeddingModelPort
from core.ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)

async def search_documents(
    request: QueryRequest,
    embedder: EmbeddingModelPort,
    vector_store: VectorStorePort
) -> dict:
    logger.info(f"Search: {request.query[:50]}")

    query_embedding = await embedder.embed_text(request.query)
    results = await vector_store.search(query_embedding, request.limit)

    if not results:
        return {"query": request.query, "answer": "No documents found", "sources": []}

    context = "\n\n".join([r.chunk.text for r in results[:3]])
    answer = f"Based on documents:\n\n{context[:800]}..."

    return {
        "query": request.query,
        "answer": answer,
        "sources": [
            {"text": r.chunk.text[:300], "score": round(r.score, 3), "metadata": r.chunk.metadata}
            for r in results
        ]
    }
EOF

# -------------------- adapters: document_parser --------------------
: > "$PROJECT/adapters/__init__.py"
: > "$PROJECT/adapters/document_parser/__init__.py"

cat > "$PROJECT/adapters/document_parser/pdf_parser.py" <<'EOF'
import fitz  # PyMuPDF
from typing import AsyncIterator
from core.ports.document_parser import DocumentParserPort

class PDFParser(DocumentParserPort):
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def parse(self, file_bytes: bytes) -> str:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    async def chunk(self, text: str) -> AsyncIterator[str]:
        words = text.split()
        step = self.chunk_size - self.overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + self.chunk_size])
            if len(chunk) > 50:
                yield chunk
EOF

# -------------------- adapters: embedding_model --------------------
: > "$PROJECT/adapters/embedding_model/__init__.py"

cat > "$PROJECT/adapters/embedding_model/sentence_transformer.py" <<'EOF'
from typing import List
import asyncio
from sentence_transformers import SentenceTransformer
from core.ports.embedding_model import EmbeddingModelPort

class SentenceTransformerModel(EmbeddingModelPort):
    _instance = None
    _model = None

    def __new__(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._model = SentenceTransformer(model_name)
        return cls._instance

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, show_progress_bar=False, batch_size=8, normalize_embeddings=True)
        )
        return [emb.tolist() for emb in embeddings]
EOF

# -------------------- adapters: vector_store --------------------
: > "$PROJECT/adapters/vector_store/__init__.py"

cat > "$PROJECT/adapters/vector_store/qdrant_store.py" <<'EOF'
from typing import List
import asyncio
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from core.ports.vector_store import VectorStorePort
from core.domain.models import Chunk, SearchResult

class QdrantStore(VectorStorePort):
    def __init__(self, url: str, collection: str, dimension: int):
        self.client = self._connect(url)
        self.collection = collection
        self.dimension = dimension
        self._ensure_collection()

    def _connect(self, url: str) -> QdrantClient:
        for attempt in range(30):
            try:
                client = QdrantClient(url=url, timeout=10)
                client.get_collections()
                return client
            except Exception as e:
                if attempt < 29:
                    time.sleep(2)
                else:
                    raise Exception(f"Qdrant connection failed: {e}")

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
            )

    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        loop = asyncio.get_event_loop()
        points = [
            PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={"text": chunk.text, "metadata": chunk.metadata}
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        await loop.run_in_executor(
            None,
            lambda: self.client.upsert(collection_name=self.collection, points=points, wait=True)
        )

    async def search(self, embedding: List[float], limit: int) -> List[SearchResult]:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=self.collection,
                query_vector=embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
        )
        return [
            SearchResult(
                chunk=Chunk(
                    id=str(r.id),
                    text=r.payload["text"],
                    metadata=r.payload["metadata"]
                ),
                score=r.score
            )
            for r in results
        ]
EOF

# -------------------- api/main.py --------------------
: > "$PROJECT/api/__init__.py"

cat > "$PROJECT/api/main.py" <<'EOF'
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging
import sys

from core.domain.models import QueryRequest
from core.usecases.ingest import ingest_document
from core.usecases.search import search_documents
from adapters.document_parser.pdf_parser import PDFParser
from adapters.embedding_model.sentence_transformer import SentenceTransformerModel
from adapters.vector_store.qdrant_store import QdrantStore

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/app.log'), logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service")

embedder = None
vector_store = None

@app.on_event("startup")
async def startup():
    global embedder, vector_store
    logger.info("Loading embedding model...")
    embedder = SentenceTransformerModel()
    logger.info(f"Model loaded: dimension={embedder.dimension}")

    logger.info("Connecting to Qdrant...")
    vector_store = QdrantStore(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection="documents",
        dimension=embedder.dimension
    )
    logger.info("Qdrant connected")

@app.get("/health")
async def health():
    return {"status": "ok", "embedder": embedder is not None, "vector_store": vector_store is not None}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Max 200MB")

    parser = PDFParser()
    result = await ingest_document(content, file.filename, parser, embedder, vector_store)
    return {"success": True, **result}

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

@app.post("/search")
async def search(req: SearchRequest):
    query_req = QueryRequest(query=req.query, limit=req.limit)
    return await search_documents(query_req, embedder, vector_store)
EOF

# -------------------- helper scripts --------------------
cat > "$PROJECT/start.sh" <<'EOF'
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous containers
docker compose down -v 2>/dev/null || true

echo "Cleaning old image (if any)..."
docker rmi rag-service-api 2>/dev/null || true

echo "Starting Qdrant..."
docker compose up -d qdrant

echo "Waiting for Qdrant (max 60s)..."
for i in {1..30}; do
  if curl -sf http://localhost:6333 >/dev/null 2>&1; then
    echo "Qdrant ready"
    break
  fi
  sleep 2
  if [ $i -eq 30 ]; then
    echo "Qdrant failed to start"; exit 1
  fi
done

echo "Building API..."
docker compose build --no-cache api

echo "Starting API..."
docker compose up -d api

echo "Waiting for API health (max 30s)..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "API ready at http://localhost:8000/docs"
    exit 0
  fi
  sleep 1
done
echo "API failed to pass health check. Run ./debug.sh"
exit 1
EOF

cat > "$PROJECT/stop.sh" <<'EOF'
#!/bin/bash
docker compose down -v
EOF

cat > "$PROJECT/debug.sh" <<'EOF'
#!/bin/bash
echo "=== Qdrant ==="
docker logs qdrant-db --tail 50 || echo "qdrant-db not running"
echo ""
echo "=== API ==="
docker logs rag-api --tail 50 || echo "rag-api not running"
echo ""
echo "=== Status ==="
docker ps -a | grep -E "qdrant-db|rag-api" || echo "No containers"
EOF

# -------------------- gitignore --------------------
cat > "$PROJECT/.gitignore" <<'EOF'
__pycache__/
*.pyc
logs/
.env
EOF

chmod +x "$PROJECT/start.sh" "$PROJECT/stop.sh" "$PROJECT/debug.sh"

echo "==> Done."
echo "Run: cd $PROJECT && ./start.sh"
