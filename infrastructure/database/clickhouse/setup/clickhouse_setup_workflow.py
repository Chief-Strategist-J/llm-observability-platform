from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy



@workflow.defn(name="ClickhouseSetupWorkflow")
class ClickhouseSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "clickhouse-setup")
        
        result = await workflow.execute_activity(
            "setup_clickhouse_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result


@workflow.defn(name="ClickhouseTeardownWorkflow")
class ClickhouseTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "clickhouse-teardown")
        
        result = await workflow.execute_activity(
            "teardown_clickhouse_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result
