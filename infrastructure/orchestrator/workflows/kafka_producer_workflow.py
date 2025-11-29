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
class KafkaProducerWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)
        
        messages = params.get("messages", [])
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        client_id = params.get("client_id", "kafka-producer-workflow")
        
        results = []
        
        if len(messages) == 1:
            result = await workflow.execute_activity(
                "send_message_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "client_id": client_id,
                    "topic": messages[0]["topic"],
                    "value": messages[0]["value"],
                    "key": messages[0].get("key"),
                    "partition": messages[0].get("partition"),
                    "headers": messages[0].get("headers"),
                    "value_serializer": params.get("value_serializer", "string"),
                    "key_serializer": params.get("key_serializer", "string")
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            results.append(result)
        else:
            result = await workflow.execute_activity(
                "send_batch_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "client_id": client_id,
                    "messages": messages,
                    "value_serializer": params.get("value_serializer", "string"),
                    "key_serializer": params.get("key_serializer", "string")
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            results.append(result)
        
        if params.get("flush", True):
            await workflow.execute_activity(
                "flush_producer_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "client_id": client_id
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
        
        successful = sum(1 for r in results if r.get("success", False))
        
        return f"Producer workflow complete: {successful}/{len(results)} successful"
