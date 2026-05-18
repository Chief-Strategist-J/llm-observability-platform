from fastapi import APIRouter
from .handlers.instrumentation import router as instrumentation_router
from .handlers.token_counting import router as token_counting_router
from .handlers.streaming import router as streaming_router

api_v1_router = APIRouter()
api_v1_router.include_router(instrumentation_router)
api_v1_router.include_router(token_counting_router)
api_v1_router.include_router(streaming_router)
