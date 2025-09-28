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
