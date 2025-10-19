"""Database Pipeline Workflow.

Defines the workflow for executing database pipeline activities. Manages Neo4j + Qdrant
stack for graph and vector database services.

"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class DatabasePipelineWorkflow:
    """Defines the workflow for executing database pipeline activities.

    Starts Neo4j and Qdrant database services.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Executes the database pipeline workflow.

        Starts:
        1. Neo4j (graph database)
        2. Qdrant (vector database)

        """
        # Start Neo4j
        await workflow.execute_activity(
            "start_neo4j_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Start Qdrant
        await workflow.execute_activity(
            "start_qdrant_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return "Database pipeline fully configured: Neo4j + Qdrant"
