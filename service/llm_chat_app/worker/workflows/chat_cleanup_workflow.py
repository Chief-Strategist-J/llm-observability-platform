import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

logger = logging.getLogger(__name__)

@workflow.defn
class ChatCleanupWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3
        )
        timeout = timedelta(minutes=10)
        logger.info("workflow ChatCleanupWorkflow start params=%s", params)
        await workflow.execute_activity("stop_chat_container_activity", params, start_to_close_timeout=timeout, retry_policy=rp)
        await workflow.execute_activity("delete_chat_container_activity", params, start_to_close_timeout=timeout, retry_policy=rp)
        await workflow.execute_activity("delete_chat_image_activity", params, start_to_close_timeout=timeout, retry_policy=rp)
        await workflow.execute_activity("stop_neo4j_dependency_activity", params, start_to_close_timeout=timeout, retry_policy=rp)
        await workflow.execute_activity("delete_neo4j_dependency_activity", params, start_to_close_timeout=timeout, retry_policy=rp)
        logger.info("workflow ChatCleanupWorkflow complete")
        return "chat_cleanup_complete"
