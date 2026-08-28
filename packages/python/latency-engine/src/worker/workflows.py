from datetime import timedelta
from temporalio import workflow

@workflow.defn(name="LatencyBaselineWorkflow")
class LatencyBaselineWorkflow:
    @workflow.run
    async def run(self, target_date_str: str | None = None, target_hour: int | None = None) -> int:
        return await workflow.execute_activity(
            "hourly_checkpoint",
            args=[target_date_str, target_hour],
            start_to_close_timeout=timedelta(seconds=120),
        )
