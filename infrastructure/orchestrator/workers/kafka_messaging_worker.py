#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from typing import Sequence, Type

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig

from infrastructure.orchestrator.workflows.kafka_producer_workflow import KafkaProducerWorkflow
from infrastructure.orchestrator.workflows.kafka_consumer_workflow import KafkaConsumerWorkflow
from infrastructure.orchestrator.workflows.kafka_topic_management_workflow import KafkaTopicManagementWorkflow
from infrastructure.orchestrator.workflows.kafka_e2e_messaging_workflow import KafkaE2EMessagingWorkflow

from infrastructure.orchestrator.activities.kafka_activity.producer_activity import (
    send_message_activity,
    send_batch_activity,
    flush_producer_activity,
    close_producer_activity
)
from infrastructure.orchestrator.activities.kafka_activity.consumer_activity import (
    poll_messages_activity,
    commit_offsets_activity,
    seek_offset_activity,
    close_consumer_activity
)
from infrastructure.orchestrator.activities.kafka_activity.topic_activity import (
    create_topic_activity,
    delete_topic_activity,
    list_topics_activity,
    describe_topic_activity,
    list_consumer_groups_activity,
    describe_consumer_group_activity
)
from infrastructure.orchestrator.activities.kafka_activity.transaction_activity import (
    begin_transaction_activity,
    send_transactional_message_activity,
    commit_transaction_activity,
    abort_transaction_activity,
    close_transaction_client_activity
)
from infrastructure.orchestrator.activities.configurations_activity.kafka_activity import (
    start_kafka_activity,
    stop_kafka_activity,
    restart_kafka_activity,
    delete_kafka_activity,
    get_kafka_status_activity
)
from infrastructure.orchestrator.activities.configurations_activity.kafka_ui_activity import (
    start_kafka_ui_activity,
    stop_kafka_ui_activity,
    restart_kafka_ui_activity,
    delete_kafka_ui_activity,
    get_kafka_ui_status_activity
)


class KafkaMessagingWorker(BaseWorker):
    @property
    def workflows(self) -> Sequence[Type]:
        return [
            KafkaProducerWorkflow,
            KafkaConsumerWorkflow,
            KafkaTopicManagementWorkflow,
            KafkaE2EMessagingWorkflow
        ]
    
    @property
    def activities(self) -> Sequence[object]:
        return [
            send_message_activity,
            send_batch_activity,
            flush_producer_activity,
            close_producer_activity,
            poll_messages_activity,
            commit_offsets_activity,
            seek_offset_activity,
            close_consumer_activity,
            create_topic_activity,
            delete_topic_activity,
            list_topics_activity,
            describe_topic_activity,
            list_consumer_groups_activity,
            describe_consumer_group_activity,
            begin_transaction_activity,
            send_transactional_message_activity,
            commit_transaction_activity,
            abort_transaction_activity,
            close_transaction_client_activity,
            start_kafka_activity,
            stop_kafka_activity,
            restart_kafka_activity,
            delete_kafka_activity,
            get_kafka_status_activity,
            start_kafka_ui_activity,
            stop_kafka_ui_activity,
            restart_kafka_ui_activity,
            delete_kafka_ui_activity,
            get_kafka_ui_status_activity
        ]


async def main():
    config = WorkerConfig(
        host="localhost",
        port=7233,
        queue="kafka-messaging-queue",
        namespace="default",
        max_concurrency=10
    )
    
    worker = KafkaMessagingWorker(config)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
