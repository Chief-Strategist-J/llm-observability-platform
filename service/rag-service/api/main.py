"""RAG Service API.

This module provides a FastAPI-based REST API for the RAG (Retrieval-Augmented
Generation) service, including endpoints for document upload, search, and health checks.

"""

import logging
import os
import sys

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..adapters.document_parser.pdf_parser import PDFParser
from ..adapters.embedding_model.sentence_transformer import (
    SentenceTransformerModel,
)
from ..adapters.vector_store.qdrant_store import QdrantStore
from ..core.domain.models import QueryRequest
from ..core.usecases.ingest import ingest_document
from ..core.usecases.search import search_documents

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service")

EMBEDDER = None
VECTOR_STORE = None


@app.on_event("startup")
async def startup():
    """
    Initialize the RAG service on startup.
    """
    global EMBEDDER, VECTOR_STORE
    logger.info("Loading embedding model...")
    EMBEDDER = SentenceTransformerModel()
    logger.info(f"Model loaded: dimension={EMBEDDER.dimension}")

    logger.info("Connecting to Qdrant...")
    VECTOR_STORE = QdrantStore(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection="documents",
        dimension=EMBEDDER.dimension,
    )
    logger.info("Qdrant connected")


@app.get("/health")
async def health():
    """
    Get the health status of the RAG service.
    """
    return {
        "status": "ok",
        "embedder": EMBEDDER is not None,
        "vector_store": VECTOR_STORE is not None,
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload and process a PDF document for ingestion into the RAG system.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Max 200MB")

    parser = PDFParser()
    result = await ingest_document(
        content, file.filename, parser, EMBEDDER, VECTOR_STORE
    )
    return {"success": True, **result}


class SearchRequest(BaseModel):
    query: str
    limit: int | None = 5


@app.post("/search")
async def search(req: SearchRequest):
    """
    Search for documents using the RAG system.
    """
    query_req = QueryRequest(query=req.query, limit=req.limit)
    return await search_documents(query_req, EMBEDDER, VECTOR_STORE)
