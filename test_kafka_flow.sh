#!/bin/bash
# Kafka Test with kafka-native (Faster startup, no console tools in container)

echo "🧹 Starting comprehensive cleanup..."

# Stop all running containers
echo "Stopping all containers..."
docker stop "$(docker ps -aq)" 2>/dev/null || true

# Remove all containers
echo "Removing all containers..."
docker rm "$(docker ps -aq)" 2>/dev/null || true

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

echo "🚀 Starting optimized Kafka test with kafka-native..."

# Start Kafka (faster with kafka-native)
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d

# Reduced wait time for faster startup
sleep 15

# Use kafka-tools container for command line operations
echo "📋 Creating kafka-tools container for CLI operations..."
docker run -d --name kafka-tools --network kafka_kafka-network apache/kafka:latest sleep 3600

# Wait for kafka-tools to be ready
sleep 5

# Create topic using kafka-tools container
echo "📝 Creating topic..."
docker exec kafka-tools /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic test --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic may already exist"

# Produce message using kafka-tools container
echo "📤 Producing message..."
echo "test message" | docker exec -i kafka-tools /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic test

# Consume message using kafka-tools container
echo "📥 Consuming message..."
timeout 3 docker exec kafka-tools /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic test --from-beginning --max-messages 1

# Clean up kafka-tools container
echo "🧹 Cleaning up kafka-tools container..."
docker stop kafka-tools 2>/dev/null || true
docker rm kafka-tools 2>/dev/null || true

echo "✅ Kafka test complete!"
echo "🛑 Stopping Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka down
