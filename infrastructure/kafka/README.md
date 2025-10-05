# Kafka Infrastructure

Lightweight Kafka setup for event-driven architecture.

## Quick Start

```bash
# Start Kafka
docker-compose -f docker-compose.kafka.yml --profile kafka up -d

# Test Kafka
./test_kafka_flow.sh

# Stop Kafka
docker-compose -f docker-compose.kafka.yml --profile kafka down
```

## Access

- **Broker**: localhost:9092

## Test

```bash
./test_kafka_flow.sh
```

See CHANGELOG.md for changes.
