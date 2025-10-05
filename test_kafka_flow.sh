#!/bin/bash
# Optimized Kafka Test - Faster startup

echo "🚀 Starting optimized Kafka test..."

# Start Kafka (now faster with kafka-native)
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d

# Reduced wait time for faster startup
sleep 15

# Create topic (fewer partitions for speed)
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic may already exist"

# Produce message
echo "test message" | docker exec -i kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test

# Consume message (shorter timeout)
timeout 3 docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning --max-messages 1

echo "✅ Kafka test complete!"
echo "🛑 Stopping Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka down
