from typing import List, Optional
from python_shared.http.pipeline.types import PipelineContext, RequestConfig
from python_shared.http.pipeline.step_admission_control import StepAdmissionControl
from python_shared.http.pipeline.step_context_isolation import StepContextIsolation
from python_shared.http.pipeline.step_ssrf_validation import StepSsrfValidation
from python_shared.http.pipeline.step_rate_limit import StepRateLimit
from python_shared.http.pipeline.step_singleflight import StepSingleflight
from python_shared.http.pipeline.step_cache_eval import StepCacheEval
from python_shared.http.pipeline.step_circuit_breaker import StepCircuitBreaker

class HttpPipelineRunner:
    def __init__(self, steps: Optional[List[any]] = None):
        self.steps = steps or [
            StepAdmissionControl(),
            StepContextIsolation(),
            StepSsrfValidation(),
            StepRateLimit(),
            StepSingleflight(),
            StepCacheEval(),
            StepCircuitBreaker(),
        ]

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        try:
            for step in self.steps:
                await step.execute(ctx)
                if ctx.cached_response is not None:
                    break
            return ctx
        finally:
            ctx.admission_control.release()

pipeline_runner = HttpPipelineRunner()
