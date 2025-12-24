from datetime import timedelta
from pathlib import Path
from temporalio import workflow
from temporalio.common import RetryPolicy



@workflow.defn(name="MongodbSetupWorkflow")
class MongodbSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "mongodb-setup")
        
        result = await workflow.execute_activity(
            "setup_mongodb_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )
        
        return result


@workflow.defn(name="MongodbTeardownWorkflow")
class MongodbTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "mongodb-teardown")
        
        result = await workflow.execute_activity(
            "teardown_mongodb_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )
        
        return result