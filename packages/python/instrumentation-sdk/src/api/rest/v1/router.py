from fastapi import APIRouter
from .handlers.instrumentation import router as instrumentation_router

api_v1_router = APIRouter()
api_v1_router.include_router(instrumentation_router)
