from __future__ import annotations

from fastapi import APIRouter

from api.rest.v1.handlers.health import router as health_router
from api.rest.v1.handlers.score import router as score_router
from api.rest.v1.handlers.scorers import router as scorers_router


router = APIRouter()
router.include_router(health_router)
router.include_router(score_router)
router.include_router(scorers_router)
