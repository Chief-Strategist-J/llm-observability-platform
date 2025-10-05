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
