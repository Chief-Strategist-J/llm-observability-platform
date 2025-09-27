"""Health check routes."""
from fastapi import APIRouter
from core.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
