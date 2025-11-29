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
class KafkaE2EMessagingWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)
        
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        topic_name = params.get("topic_name", "test-topic")
        test_messages_count = params.get("test_messages_count", 10)
        
        await workflow.execute_activity(
            "start_kafka_activity",
            {"instance_id": params.get("instance_id", 0)},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        await workflow.execute_activity(
            "start_kafka_ui_activity",
            {"instance_id": params.get("instance_id", 0)},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        await workflow.execute_activity(
            "create_topic_activity",
            {
                "bootstrap_servers": bootstrap_servers,
                "topic_name": topic_name,
                "num_partitions": params.get("num_partitions", 3),
                "replication_factor": params.get("replication_factor", 1)
            },
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        messages = []
        for i in range(test_messages_count):
            messages.append({
                "topic": topic_name,
                "value": f"test-message-{i}",
                "key": f"key-{i % 3}"
            })
        
        await workflow.execute_activity(
            "send_batch_activity",
            {
                "bootstrap_servers": bootstrap_servers,
                "messages": messages,
                "client_id": "e2e-producer"
            },
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        consumer_result = await workflow.execute_activity(
            "poll_messages_activity",
            {
                "bootstrap_servers": bootstrap_servers,
                "group_id": "e2e-consumer-group",
                "topics": [topic_name],
                "client_id": "e2e-consumer",
                "timeout_ms": 5000,
                "max_records": test_messages_count,
                "auto_offset_reset": "earliest"
            },
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        consumed_count = consumer_result.get("messages_count", 0)
        
        if params.get("cleanup", True):
            await workflow.execute_activity(
                "close_consumer_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "group_id": "e2e-consumer-group",
                    "client_id": "e2e-consumer"
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            
            await workflow.execute_activity(
                "close_producer_activity",
                {
                    "bootstrap_servers": bootstrap_servers,
                    "client_id": "e2e-producer"
                },
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            
            await workflow.execute_activity(
                "stop_kafka_ui_activity",
                {"instance_id": params.get("instance_id", 0)},
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
        
        return f"E2E workflow complete: sent {test_messages_count}, consumed {consumed_count} messages"
