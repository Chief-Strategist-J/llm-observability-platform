from fastapi import APIRouter
from .handlers.instrumentation import router as instrumentation_router
from .handlers.token_counting import router as token_counting_router
from .handlers.streaming import router as streaming_router
from .handlers.pii_injection import router as pii_injection_router
from .handlers.metrics import router as metrics_router
from .handlers.deterministic_sampling import router as deterministic_sampling_router
from .handlers.minilm_embedding import router as minilm_embedding_router
from .handlers.spans import router as spans_router

api_v1_router = APIRouter()
api_v1_router.include_router(instrumentation_router)
api_v1_router.include_router(token_counting_router)
api_v1_router.include_router(streaming_router)
api_v1_router.include_router(pii_injection_router)
api_v1_router.include_router(metrics_router)
api_v1_router.include_router(deterministic_sampling_router)
api_v1_router.include_router(minilm_embedding_router)
api_v1_router.include_router(spans_router)


