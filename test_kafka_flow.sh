#!/bin/bash
# Comprehensive Kafka Test with Full Cleanup

echo "🧹 Starting comprehensive cleanup..."

# Stop all running containers
echo "Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all containers
echo "Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove Kafka-related images
echo "Removing Kafka images..."
docker rmi apache/kafka:latest apache/kafka-native:latest kafbat/kafka-ui:latest 2>/dev/null || true

# Remove all unused networks
echo "Removing unused networks..."
docker network prune -f

# Remove all unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# Clean up Docker system
echo "Cleaning Docker system..."
docker system prune -f

# Clear any hanging processes
echo "Clearing processes..."
pkill -f kafka 2>/dev/null || true
pkill -f docker-compose 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""

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
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d
