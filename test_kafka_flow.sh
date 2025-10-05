#!/bin/bash
# Minimal Kafka Test

echo "Starting Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d

sleep 10

echo "Creating topic..."
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test --partitions 1 --replication-factor 1

echo "Producing message..."
echo "test message" | docker exec -i kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test

echo "Consuming message..."
timeout 5 docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning --max-messages 1

echo "Stopping Kafka..."
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka down

echo "✅ Kafka test complete!"
