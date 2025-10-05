#!/bin/bash
# Simple Kafka Event Flow Test

echo "🚀 Starting Kafka Event Flow Test..."

# Start Kafka
echo "Starting Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d

# Wait for Kafka to be ready
sleep 10

# Create test topic
echo "Creating test topic..."
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test-events --partitions 1 --replication-factor 1

# Produce a test message
echo "Producing test message..."
echo "test_event: Hello from Kafka!" | docker exec -i kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test-events

# Consume the message
echo "Consuming test message..."
timeout 5 docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test-events --from-beginning --max-messages 1

echo "✅ Kafka Event Flow Test Complete!"
echo "🛑 Stopping Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka down
