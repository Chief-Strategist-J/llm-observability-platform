#!/bin/bash
set -e

# Kafka broker address (internal Docker network address)
KAFKA_BROKER=${1:-"localhost:9094"}

echo "Initializing Kafka topics for Instrumentation Layer..."

# Topic format: "name:partitions:replication_factor"
TOPICS=(
  "llm.spans.raw.unvalidated:3:1"
  "llm.spans.raw:3:1"
  "llm.spans.raw.dlq:1:1"
  "llm.spans.sampled:3:1"
)

for topic_config in "${TOPICS[@]}"; do
  IFS=':' read -r name partitions replication <<< "$topic_config"
  
  echo "Checking topic: $name"
  # We use --if-not-exists to ensure we don't error if it's already there
  docker exec -t docker-kafka-1 kafka-topics --create --if-not-exists \
    --bootstrap-server kafka:29092 \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor "$replication"
done

echo "Kafka topic initialization completed."
