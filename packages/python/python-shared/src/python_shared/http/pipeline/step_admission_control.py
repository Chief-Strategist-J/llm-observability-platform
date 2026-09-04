from python_shared.http.pipeline.types import PipelineContext

class StepAdmissionControl:
    name: str = "AdmissionControl"
    description: str = "Concurrency Admission Control & Fleet Capacity Guard"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        if not ctx.admission_control.acquire():
            active_count = ctx.admission_control.get_active_count()
            raise RuntimeError(f"Too Many Requests - Fleet In-Flight Concurrency Capacity ({active_count}) Exceeded")
