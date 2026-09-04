from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.http.pipeline.types import PipelineContext

class StepCacheEval:
    name: str = "CacheEval"
    description: str = "Tenant Partitioned LRU Cache Lookup & Invalidation"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        method = ctx.config.method.upper()

        if method in (
            HTTP_CONSTANTS.METHOD_POST,
            HTTP_CONSTANTS.METHOD_PUT,
            HTTP_CONSTANTS.METHOD_PATCH,
            HTTP_CONSTANTS.METHOD_DELETE,
        ):
            ctx.cache_store.clear(ctx.tenant_id)
            return

        if method == HTTP_CONSTANTS.METHOD_GET and not ctx.config.no_cache and ctx.hashed_request_key:
            cached = ctx.cache_store.get(ctx.tenant_id, ctx.hashed_request_key)
            if cached is not None:
                ctx.cached_response = cached
