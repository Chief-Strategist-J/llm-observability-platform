from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class DatabasePipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, service_name: str) -> str:
        await workflow.execute_activity(
            "start_neo4j_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        await workflow.execute_activity(
            "start_qdrant_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return "Database pipeline fully configured: Neo4j + Qdrant"
