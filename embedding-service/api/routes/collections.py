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
