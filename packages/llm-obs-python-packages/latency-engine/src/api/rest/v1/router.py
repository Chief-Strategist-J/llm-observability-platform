from __future__ import annotations

from fastapi import APIRouter

from api.rest.v1.handlers.health import router as health_router
from api.rest.v1.handlers.latency import router as latency_router

router = APIRouter()

# Mount health endpoint at the root level /health
router.include_router(health_router)

# Mount latency query endpoints under the /v1 prefix as defined by the OpenAPI spec
router.include_router(latency_router, prefix="/v1")
