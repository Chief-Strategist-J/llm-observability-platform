from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from opentelemetry import trace
from .....features.minilm_embedding.index import get_embedding

router = APIRouter(prefix="/embeddings", tags=["MiniLM Embedding"])

class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: list[float]

def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "minilm_embedding")

@router.post("/embed", response_model=EmbeddingResponse)
async def embed_endpoint(request: EmbeddingRequest) -> EmbeddingResponse:
    _set_span_attributes()
    try:
        emb = await get_embedding(request.text)
        if emb is None:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        return EmbeddingResponse(embedding=emb)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
