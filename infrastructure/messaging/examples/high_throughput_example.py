"""
High-Throughput Kafka Usage Examples

This file demonstrates how to use the high-throughput Kafka adapters
to handle 1M+ messages efficiently with batching, compression, and parallel processing.
"""

from infrastructure.adapters.kafka_producer_adapter import (
    HighThroughputKafkaProducer, 
    KafkaProducerConfig
)
from infrastructure.adapters.kafka_consumer_adapter import (
    HighThroughputKafkaConsumer,
    KafkaConsumerConfig
)
from domain.clients.producer_client import ProducerDomainClient
from domain.clients.consumer_client import ConsumerDomainClient
import asyncio


def example_1_batch_produce():
    """
    Example 1: Batch produce 1M messages
    Expected time: ~10-60 seconds with proper Kafka cluster
    """
    config = KafkaProducerConfig(
        bootstrap_servers="localhost:9092",
        batch_size=131072,  # 128KB
        linger_ms=20,  # Wait 20ms to batch
        compression_type="snappy",  # Compression
        acks="1",  # Leader ack for speed
        max_in_flight_requests_per_connection=10
    )
    
    producer = HighThroughputKafkaProducer(config)
    client = ProducerDomainClient(producer)
    
    # Generate 1M messages
    messages = [
        {"topic": "high-throughput-topic", "partition": 0, "offset": i, 
         "key": f"key-{i}", "value": f"value-{i}"}
        for i in range(1000000)
    ]
    
    # Send in batches of 10,000
    batch_size = 10000
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        results = producer.produce_batch("high-throughput-topic", batch)
        print(f"Sent batch {i//batch_size + 1}/{len(messages)//batch_size}")
    
    producer.flush()
    producer.close()
    print("All 1M messages sent!")


def example_2_async_produce():
    """
    Example 2: Async produce for non-blocking operations
    """
    config = KafkaProducerConfig(
        bootstrap_servers="localhost:9092",
        batch_size=65536,
        linger_ms=10,
        compression_type="lz4"
    )
    
    producer = HighThroughputKafkaProducer(config)
    
    async def send_async():
        tasks = []
        for i in range(10000):
            future = producer.produce_async(
                topic="async-topic",
                key=f"key-{i}",
                value=f"value-{i}",
                partition=None,
                headers={}
            )
            tasks.append(future)
        
        results = await asyncio.gather(*tasks)
        print(f"Sent {len(results)} messages asynchronously")
    
    asyncio.run(send_async())
    producer.close()


def example_3_parallel_consume():
    """
    Example 3: Parallel consume from multiple partitions
    """
    config = KafkaConsumerConfig(
        bootstrap_servers="localhost:9092",
        group_id="high-throughput-consumer",
        max_poll_records=500,
        max_threads=10
    )
    
    consumer = HighThroughputKafkaConsumer(config)
    client = ConsumerDomainClient(consumer)
    
    # Consume from 10 partitions in parallel
    partitions = list(range(10))
    results = consumer.consume_parallel(
        topic="high-throughput-topic",
        consumer_group="high-throughput-consumer",
        partitions=partitions,
        max_messages_per_partition=1000,
        timeout_ms=5000
    )
    
    total_messages = sum(len(msgs) for msgs in results.values())
    print(f"Consumed {total_messages} messages from {len(results)} partitions")
    
    consumer.close()


def example_4_stream_consume():
    """
    Example 4: Stream consume with batch processing
    """
    config = KafkaConsumerConfig(
        bootstrap_servers="localhost:9092",
        group_id="stream-consumer",
        max_poll_records=1000,
        batch_size=100
    )
    
    consumer = HighThroughputKafkaConsumer(config)
    
    def process_batch(messages):
        print(f"Processing batch of {len(messages)} messages")
        # Process messages here (e.g., save to database)
        # consumer.commit_offsets_batch(...)
    
    # Start streaming
    consumer.consume_stream(
        topic="high-throughput-topic",
        consumer_group="stream-consumer",
        message_handler=process_batch,
        batch_size=100
    )
    
    # Keep running...
    # consumer.stop_stream()
    # consumer.close()


def example_5_http_api_batch():
    """
    Example 5: Use HTTP API for batch operations
    """
    import httpx
    
    # Prepare 10,000 messages
    messages = [
        {
            "topic": "api-topic",
            "key": f"key-{i}",
            "value": f"value-{i}",
            "partition": 0,
            "headers": {}
        }
        for i in range(10000)
    ]
    
    # Send via HTTP API
    response = httpx.post(
        "http://localhost:8001/api/v1/producer/produce/batch",
        json={"messages": messages},
        headers={"Authorization": "Bearer your-token"}
    )
    
    result = response.json()
    print(f"Sent {result['count']} messages via HTTP API")


def example_6_optimal_kafka_setup():
    """
    Example 6: Optimal Kafka configuration for 1M messages
    """
    # Producer config for maximum throughput
    producer_config = KafkaProducerConfig(
        bootstrap_servers="kafka-broker1:9092,kafka-broker2:9092,kafka-broker3:9092",
        batch_size=131072,  # 128KB
        linger_ms=20,  # 20ms batching
        compression_type="snappy",  # Fast compression
        acks="1",  # Leader ack (balance speed/durability)
        max_in_flight_requests_per_connection=10,
        buffer_memory=67108864,  # 64MB buffer
        retries=3,
        enable_idempotence=True,
        max_request_size=10485760  # 10MB
    )
    
    # Consumer config for maximum throughput
    consumer_config = KafkaConsumerConfig(
        bootstrap_servers="kafka-broker1:9092,kafka-broker2:9092,kafka-broker3:9092",
        group_id="high-throughput-group",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=1000,  # Large batch size
        max_poll_interval_ms=300000,
        session_timeout_ms=10000,
        heartbeat_interval_ms=3000,
        fetch_min_bytes=1024,  # 1KB minimum fetch
        fetch_max_wait_ms=500,
        fetch_max_bytes=104857600,  # 100MB
        max_partition_fetch_bytes=10485760,  # 10MB per partition
        max_threads=20  # Parallel consumers
    )
    
    print("Optimal Kafka configuration for 1M+ messages:")
    print(f"Producer: batch_size={producer_config.batch_size}, compression={producer_config.compression_type}")
    print(f"Consumer: max_poll_records={consumer_config.max_poll_records}, max_threads={consumer_config.max_threads}")


if __name__ == "__main__":
    print("High-Throughput Kafka Examples")
    print("=" * 50)
    print("\nExample 1: Batch produce 1M messages")
    print("Example 2: Async produce")
    print("Example 3: Parallel consume")
    print("Example 4: Stream consume")
    print("Example 5: HTTP API batch")
    print("Example 6: Optimal Kafka setup")
    print("\nRun individual examples to test.")
    
    # Example 6 shows the optimal configuration
    example_6_optimal_kafka_setup()
