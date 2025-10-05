#!/usr/bin/env python3
"""
Minimal Kafka Event Flow Test
Tests basic producer/consumer functionality
"""

import json
import time
from kafka import KafkaProducer, KafkaConsumer

def test_kafka_flow():
    """Test basic Kafka event flow"""
    print("🧪 Testing Kafka Event Flow...")

    # Test data
    test_event = {
        "event_type": "test",
        "message": "Hello Kafka!",
        "timestamp": time.time()
    }

    # Producer
    print("📤 Producing test event...")
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    producer.send('test-events', value=test_event)
    producer.flush()
    print(f"✅ Sent: {test_event}")

    # Consumer
    print("📥 Consuming test event...")
    consumer = KafkaConsumer(
        'test-events',
        bootstrap_servers=['localhost:9092'],
        group_id='test-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000
    )

    # Read one message
    for message in consumer:
        received_event = message.value
        print(f"✅ Received: {received_event}")

        # Verify it's the same message
        if received_event['message'] == test_event['message']:
            print("🎉 Event Flow Test PASSED!")
            return True
        else:
            print("❌ Event Flow Test FAILED!")
            return False

    print("❌ No message received - Test FAILED!")
    return False

if __name__ == "__main__":
    try:
        test_kafka_flow()
    except Exception as e:
        print(f"❌ Test Error: {e}")
        print("💡 Make sure Kafka is running: docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d")
