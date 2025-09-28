#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="rag-service"

echo "🚀 Creating minimal RAG service..."

mkdir -p "$PROJECT_NAME"
mkdir -p "$PROJECT_NAME/data/qdrant"
mkdir -p "$PROJECT_NAME/api/routes"
mkdir -p "$PROJECT_NAME/core"
mkdir -p "$PROJECT_NAME/services"

cat > "$PROJECT_NAME/docker-compose.yml" << 'EOF'
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-db
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
    restart: unless-stopped
    profiles: ["active"]

  rag-api:
    build: .
    container_name: rag-api
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - qdrant
    volumes:
      - .:/app
    restart: unless-stopped
    profiles: ["active"]
EOF

cat > "$PROJECT_NAME/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
EOF

cat > "$PROJECT_NAME/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
pymupdf==1.23.14
python-multipart==0.0.6
numpy==1.24.3
torch==2.0.1+cpu
--extra-index-url https://download.pytorch.org/whl/cpu
EOF

cat > "$PROJECT_NAME/main.py" << 'EOF'
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from api.routes import upload_pdf, search_rag
from core.config import settings

app: FastAPI = FastAPI(
    title="RAG Service", 
    version="1.0.0",
    timeout=300
)

app.include_router(upload_pdf.router)
app.include_router(search_rag.router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

cat > "$PROJECT_NAME/core/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/core/config.py" << 'EOF'
import os

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    VECTOR_SIZE: int = 384
    COLLECTION_NAME: str = "documents"
    MODEL_NAME: str = "all-MiniLM-L6-v2"

settings: Settings = Settings()
EOF

cat > "$PROJECT_NAME/core/models.py" << 'EOF'
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Document:
    id: str
    text: str
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]
EOF

cat > "$PROJECT_NAME/services/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/services/pdf_processor.py" << 'EOF'
import fitz
from typing import List
from io import BytesIO
import gc

class PDFProcessor:
    def extract_text(self, pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text: str = ""
            
            total_pages: int = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text: str = page.get_text()
                text += page_text + "\n"
                
                if page_num % 50 == 0:
                    gc.collect()
            
            doc.close()
            gc.collect()
            
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        if not text.strip():
            return []
            
        words: List[str] = text.split()
        chunks: List[str] = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words: List[str] = words[i:i + chunk_size]
            chunk: str = " ".join(chunk_words)
            
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
EOF

cat > "$PROJECT_NAME/services/embedding_service.py" << 'EOF'
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model: SentenceTransformer = SentenceTransformer(settings.MODEL_NAME)
    
    def embed_text(self, text: str) -> List[float]:
        embedding: np.ndarray = self.model.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings: np.ndarray = self.model.encode(texts)
        return embeddings.tolist()
EOF

cat > "$PROJECT_NAME/services/qdrant_service.py" << 'EOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from typing import List, Dict, Any
import uuid
import gc
from core.config import settings
from core.models import Document, SearchResult

class QdrantService:
    def __init__(self):
        self.client: QdrantClient = QdrantClient(url=settings.QDRANT_URL, timeout=300)
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(settings.COLLECTION_NAME)
        except:
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
    
    def upsert_documents_batch(self, documents: List[Document], embeddings: List[List[float]], batch_size: int = 100) -> bool:
        try:
            total_docs: int = len(documents)
            
            for i in range(0, total_docs, batch_size):
                batch_docs: List[Document] = documents[i:i + batch_size]
                batch_embeddings: List[List[float]] = embeddings[i:i + batch_size]
                
                points: List[PointStruct] = []
                
                for doc, embedding in zip(batch_docs, batch_embeddings):
                    point: PointStruct = PointStruct(
                        id=doc.id,
                        vector=embedding,
                        payload={
                            "text": doc.text,
                            "metadata": doc.metadata
                        }
                    )
                    points.append(point)
                
                self.client.upsert(
                    collection_name=settings.COLLECTION_NAME,
                    points=points,
                    wait=True
                )
                
                points.clear()
                gc.collect()
            
            return True
        except Exception as e:
            print(f"Upsert error: {e}")
            return False
    
    def search(self, query_vector: List[float], limit: int = 5) -> List[SearchResult]:
        try:
            results = self.client.query_points(
                collection_name=settings.COLLECTION_NAME,
                query=query_vector,
                limit=limit,
                with_payload=True
            )
            
            search_results: List[SearchResult] = []
            for point in results.points:
                result: SearchResult = SearchResult(
                    id=str(point.id),
                    text=point.payload["text"],
                    score=float(point.score),
                    metadata=point.payload["metadata"]
                )
                search_results.append(result)
            
            return search_results
        except:
            return []
EOF

cat > "$PROJECT_NAME/services/rag_service.py" << 'EOF'
from typing import List
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from core.models import SearchResult

class RAGService:
    def __init__(self):
        self.embedding_service: EmbeddingService = EmbeddingService()
        self.qdrant_service: QdrantService = QdrantService()
    
    def search_and_generate(self, query: str, limit: int = 3) -> dict[str, any]:
        query_embedding: List[float] = self.embedding_service.embed_text(query)
        search_results: List[SearchResult] = self.qdrant_service.search(query_embedding, limit)
        
        if not search_results:
            return {
                "answer": "No relevant documents found.",
                "sources": []
            }
        
        context: str = "\n\n".join([result.text for result in search_results])
        
        answer: str = f"Based on the available documents:\n\n{context}"
        
        sources: List[dict] = [
            {
                "id": result.id,
                "score": result.score,
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text
            }
            for result in search_results
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query
        }
EOF

cat > "$PROJECT_NAME/api/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/api/routes/__init__.py" << 'EOF'
EOF

cat > "$PROJECT_NAME/api/routes/upload_pdf.py" << 'EOF'
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uuid
from services.pdf_processor import PDFProcessor
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from core.models import Document

router: APIRouter = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        pdf_bytes: bytes = await file.read()
        
        processor: PDFProcessor = PDFProcessor()
        text: str = processor.extract_text(pdf_bytes)
        chunks: list[str] = processor.chunk_text(text)
        
        embedding_service: EmbeddingService = EmbeddingService()
        embeddings: list[list[float]] = embedding_service.embed_batch(chunks)
        
        documents: list[Document] = []
        for i, chunk in enumerate(chunks):
            doc: Document = Document(
                id=f"{file.filename}_{i}",
                text=chunk,
                metadata={"filename": file.filename, "chunk": i}
            )
            documents.append(doc)
        
        qdrant_service: QdrantService = QdrantService()
        success: bool = qdrant_service.upsert_documents(documents, embeddings)
        
        if success:
            return JSONResponse({
                "message": "PDF processed successfully",
                "chunks": len(chunks),
                "filename": file.filename
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to store embeddings")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
EOF

cat > "$PROJECT_NAME/api/routes/search_rag.py" << 'EOF'
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_service import RAGService

router: APIRouter = APIRouter(prefix="/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str

@router.post("/rag")
async def search_rag(request: SearchRequest) -> dict[str, any]:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        rag_service: RAGService = RAGService()
        result: dict[str, any] = rag_service.search_and_generate(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
EOF

cat > "$PROJECT_NAME/.gitignore" << 'EOF'
__pycache__/
*.pyc
.env
data/qdrant/*
!data/qdrant/.gitkeep
.DS_Store
*.log
EOF

touch "$PROJECT_NAME/data/qdrant/.gitkeep"

cat > "$PROJECT_NAME/start.sh" << 'EOF'
#!/bin/bash
echo "Starting RAG service..."
docker-compose --profile active up -d
echo "Service started at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
EOF

cat > "$PROJECT_NAME/stop.sh" << 'EOF'
#!/bin/bash
echo "Stopping RAG service..."
docker-compose --profile active down
echo "Service stopped"
EOF

chmod +x "$PROJECT_NAME/start.sh"
chmod +x "$PROJECT_NAME/stop.sh"

cat > "$PROJECT_NAME/README.md" << 'EOF'
# RAG Service

Minimal RAG service with PDF processing and Qdrant vector database.

## Quick Start

```bash
# Start service
./start.sh

# Stop service
./stop.sh
```

## API Endpoints

1. **Upload PDF**: `POST /upload/pdf`
   - Upload PDF file for processing and embedding

2. **Search RAG**: `POST /search/rag`
   - Query: `{"query": "your question"}`
   - Returns answer with sources

## Access
- API: http://localhost:8000/docs
- Qdrant: http://localhost:6333/dashboard

## Usage

1. Start service with `./start.sh`
2. Upload PDF via `/upload/pdf`
3. Query via `/search/rag`
4. Stop service with `./stop.sh`
EOF

echo "✅ RAG service created successfully!"
echo ""
echo "📋 Commands:"
echo "cd $PROJECT_NAME"
echo "./start.sh    # Start service"
echo "./stop.sh     # Stop service"
echo ""
echo "🌐 URLs:"
echo "- API: http://localhost:8000/docs"
echo "- Qdrant: http://localhost:6333/dashboard"