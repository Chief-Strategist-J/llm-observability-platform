#!/usr/bin/env python3

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("kafka_database_trigger")


class KafkaDatabasePipeline(PipelineExecutor):
    pass


async def run_database_setup():
    config = WorkflowConfig(
        service_name="kafka_database",
        workflow_name="KafkaMangoDBDatabaseWorkflow",
        task_queue="kafka_mango_database-queue",
        params={
            "service_name": "kafka_database",
            "instance_id": 0
        }
    )
    
    logger.info("🚀 Starting Kafka Database Infrastructure")
    logger.info("   Services: Traefik, Kafka, MongoDB, Mongo Express")
    
    pipeline = KafkaDatabasePipeline(config=config)
    await pipeline.run_pipeline()
    
    logger.info("✅ Database infrastructure started successfully")


async def run_kafka_e2e_test():
    config = WorkflowConfig(
        service_name="kafka-e2e-test",
        workflow_name="KafkaE2EMessagingWorkflow",
        task_queue="kafka-messaging-queue",
        params={
            "topic_name": "e2e-test-topic",
            "test_messages_count": 10,
            "num_partitions": 3,
            "instance_id": 0,
            "cleanup": True
        }
    )
    
    logger.info("🚀 Starting Kafka E2E Messaging Test")
    logger.info(f"   Topic: {config.params['topic_name']}")
    logger.info(f"   Messages: {config.params['test_messages_count']}")
    logger.info(f"   Partitions: {config.params['num_partitions']}")
    
    pipeline = KafkaDatabasePipeline(config=config)
    await pipeline.run_pipeline()
    
    logger.info("✅ Kafka E2E test completed successfully")


async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await run_kafka_e2e_test()
    else:
        await run_database_setup()


if __name__ == "__main__":
    asyncio.run(main())
