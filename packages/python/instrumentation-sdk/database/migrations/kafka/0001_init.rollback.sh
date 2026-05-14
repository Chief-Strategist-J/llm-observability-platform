#!/bin/bash
# migration:      0001
# description:    rollback initial kafka topics
# author:         antigravity
# date:           2026-05-14
# reversible:     YES

set -e

TOPICS=(
  "llm.spans.raw.unvalidated"
  "llm.spans.raw"
  "llm.spans.raw.dlq"
  "llm.spans.sampled"
)

for name in "${TOPICS[@]}"; do
  echo "Deleting topic: $name"
  docker exec -t docker-kafka-1 kafka-topics --delete --if-exists --bootstrap-server kafka:29092 --topic "$name"
done

echo "Kafka rollback completed."
