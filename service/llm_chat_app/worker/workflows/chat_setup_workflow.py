import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

logger = logging.getLogger(__name__)

@workflow.defn
class ChatSetupWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3
        )
        timeout = timedelta(minutes=10)

        p = dict(params)
        p["context"] = "/home/j/live/dinesh/llm-chatbot-python/service/llm_chat_app"

        logger.info("workflow ChatSetupWorkflow start params=%s", p)

        await workflow.execute_activity(
            "start_neo4j_dependency_activity", p, start_to_close_timeout=timeout, retry_policy=rp
        )
        # await workflow.execute_activity(
        #     "verify_cloudflare_dependency_activity", p, start_to_close_timeout=timeout, retry_policy=rp
        # )
        # await workflow.execute_activity(
        #     "build_chat_image_activity", p, start_to_close_timeout=timeout, retry_policy=rp
        # )
        # await workflow.execute_activity(
        #     "run_chat_container_activity", p, start_to_close_timeout=timeout, retry_policy=rp
        # )
        # await workflow.execute_activity(
        #     "check_chat_health_activity", p, start_to_close_timeout=timeout, retry_policy=rp
        # )

        logger.info("workflow ChatSetupWorkflow complete")
        return "chat_setup_complete"
