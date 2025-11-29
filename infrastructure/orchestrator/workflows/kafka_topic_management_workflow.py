import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class KafkaTopicManagementWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)
        
        operation = params.get("operation", "create")
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        
        if operation == "create":
            result = await workflow.execute_activity(
                "create_topic_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "topic_name": params["topic_name"],
                    "num_partitions": params.get("num_partitions", 1),
                    "replication_factor": params.get("replication_factor", 1),
                    "config": params.get("config", {})
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            return f"Topic created: {result}"
        
        elif operation == "delete":
            result = await workflow.execute_activity(
                "delete_topic_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "topics": params["topics"]
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            return f"Topics deleted: {result}"
        
        elif operation == "list":
            result = await workflow.execute_activity(
                "list_topics_activity",
                {
                    "bootstrap_servers": bootstrap_servers
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            return f"Topics listed: {result.get('count', 0)} topics"
        
        elif operation == "describe":
            result = await workflow.execute_activity(
                "describe_topic_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "topics": params["topics"]
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            return f"Topics described: {result}"
        
        else:
            return f"Unknown operation: {operation}"
