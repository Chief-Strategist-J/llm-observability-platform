from __future__ import annotations
import asyncio
import logging
import os
import signal
import json
import redis
from confluent_kafka import Consumer, KafkaError

from config import load_config
from handlers.latency_handler import LatencyHandler

logger = logging.getLogger(__name__)

async def run() -> None:
    cfg = load_config()
    
    # Initialize redis and handler
    redis_client = redis.from_url(cfg.redis_url)
    handler = LatencyHandler(redis_client, cfg.slo_config_path)

    consumer = Consumer({
        "bootstrap.servers": cfg.kafka_bootstrap_servers,
        "group.id": cfg.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False, # manual commit to control batches
    })
    
    consumer.subscribe([cfg.kafka_topic_input])
    logger.info("latency-engine consumer started on topic=%s group=%s", cfg.kafka_topic_input, cfg.kafka_consumer_group)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, stop.set)
    loop.add_signal_handler(signal.SIGINT, stop.set)

    # Poll and process loop
    try:
        while not stop.is_set():
            # Batch: process 500 spans per Kafka poll
            spans_batch = []
            kafka_messages = []
            
            # Read messages until we hit 500 or timeout
            for _ in range(500):
                msg = await loop.run_in_executor(None, lambda: consumer.poll(timeout=0.1))
                if msg is None:
                    break
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Kafka error: %s", msg.error())
                    continue
                
                kafka_messages.append(msg)
                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                    spans_batch.append(payload)
                except Exception as e:
                    logger.error("Failed to parse span JSON: %s", e)

            if spans_batch:
                try:
                    handler.handle_spans(spans_batch)
                except Exception as e:
                    logger.error("Failed to process span batch: %s", e)
                
                # Manual commit of offset after handling batch
                # Commit Kafka offset even during Redis outage (don't block Kafka progress) (F-L-06)
                try:
                    await loop.run_in_executor(None, lambda: consumer.commit(asynchronous=False))
                except Exception as e:
                    logger.error("Failed to commit Kafka offset: %s", e)
            else:
                await asyncio.sleep(0.05)
                
    finally:
        consumer.close()
        logger.info("latency-engine consumer closed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
