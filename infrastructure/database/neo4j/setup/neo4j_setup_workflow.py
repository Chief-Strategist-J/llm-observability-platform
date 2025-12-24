from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy



@workflow.defn(name="Neo4jSetupWorkflow")
class Neo4jSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "neo4j-setup")
        
        result = await workflow.execute_activity(
            "setup_neo4j_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result


@workflow.defn(name="Neo4jTeardownWorkflow")
class Neo4jTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "neo4j-teardown")
        
        result = await workflow.execute_activity(
            "teardown_neo4j_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result
