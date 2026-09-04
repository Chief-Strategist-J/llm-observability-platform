from python_shared.http.pipeline.types import PipelineContext

class StepRateLimit:
    name: str = "RateLimit"
    description: str = "Per-Tenant Token Bucket Outbound Rate Limiting"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        if not ctx.rate_limiter.allow_request(ctx.tenant_id):
            raise RuntimeError(f"Rate limit exceeded for tenant {ctx.tenant_id}")
        ctx.retry_budget.record_request()
