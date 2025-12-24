from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy



@workflow.defn(name="MinioSetupWorkflow")
class MinioSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "minio-setup")
        
        result = await workflow.execute_activity(
            "setup_minio_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result


@workflow.defn(name="MinioTeardownWorkflow")
class MinioTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "minio-teardown")
        
        result = await workflow.execute_activity(
            "teardown_minio_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result
