import hashlib
import json
from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.http.pipeline.types import PipelineContext

def generate_hashed_key(tenant_id: str, method: str, url: str, body: any) -> str:
    raw = f"{tenant_id}:{method}:{url}:{json.dumps(body) if body else ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class StepSingleflight:
    name: str = "Singleflight"
    description: str = "SHA-256 Concurrent Request Collapsing & Deduplication"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        ctx.hashed_request_key = generate_hashed_key(
            ctx.tenant_id,
            ctx.config.method,
            ctx.config.url,
            ctx.config.body
        )

        if not ctx.config.cancel_previous and ctx.config.method == HTTP_CONSTANTS.METHOD_GET:
            existing = ctx.in_flight_singleflights.get(ctx.hashed_request_key)
            if existing:
                ctx.singleflight_hit = True
