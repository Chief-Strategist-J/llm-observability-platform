from __future__ import annotations

from fastapi import APIRouter

from api.rest.v1.handlers.health import router as health_router
from api.rest.v1.handlers.nli import router as nli_router

router = APIRouter()
router.include_router(health_router)
router.include_router(nli_router)
