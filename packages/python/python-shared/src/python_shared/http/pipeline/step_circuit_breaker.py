from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.http.pipeline.types import PipelineContext

class StepCircuitBreaker:
    name: str = "CircuitBreaker"
    description: str = "Bounded LRU Circuit Breaker State Verification"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        ctx.route_template = ctx.config.url
        ctx.circuit_key = ctx.circuit_breaker.get_circuit_key(ctx.tenant_id, ctx.route_template)

        if not ctx.circuit_breaker.can_execute(ctx.circuit_key):
            state = ctx.circuit_breaker.get_state(ctx.circuit_key)
            state_name = state.state if state else HTTP_CONSTANTS.CIRCUIT_OPEN
            raise RuntimeError(f"Circuit breaker is {state_name} for key {ctx.circuit_key}")
