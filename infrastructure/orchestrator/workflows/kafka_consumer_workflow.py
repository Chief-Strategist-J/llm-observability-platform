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
class KafkaConsumerWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)
        
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_id = params["group_id"]
        topics = params["topics"]
        client_id = params.get("client_id", "kafka-consumer-workflow")
        poll_count = params.get("poll_count", 1)
        timeout_ms = params.get("timeout_ms", 1000)
        max_records = params.get("max_records", 500)
        
        all_messages = []
        
        for i in range(poll_count):
            result = await workflow.execute_activity(
                "poll_messages_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "group_id": group_id,
                    "topics": topics,
                    "client_id": client_id,
                    "timeout_ms": timeout_ms,
                    "max_records": max_records,
                    "value_deserializer": params.get("value_deserializer", "string"),
                    "key_deserializer": params.get("key_deserializer", "string"),
                    "enable_auto_commit": params.get("enable_auto_commit", True),
                    "auto_offset_reset": params.get("auto_offset_reset", "latest")
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            
            if result.get("success"):
                messages = result.get("messages", [])
                all_messages.extend(messages)
        
        if not params.get("enable_auto_commit", True) and all_messages:
            await workflow.execute_activity(
                "commit_offsets_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "group_id": group_id,
                    "client_id": client_id
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
        
        if params.get("close_consumer", False):
            await workflow.execute_activity(
                "close_consumer_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "group_id": group_id,
                    "client_id": client_id
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
        
        return f"Consumer workflow complete: consumed {len(all_messages)} messages"
