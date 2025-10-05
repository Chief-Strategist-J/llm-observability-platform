# Kafka Infrastructure

Lightweight Kafka setup for event-driven architecture.

## Quick Start

```bash
# Start Kafka + UI
docker-compose -f docker-compose.kafka.yml --profile kafka up -d

# Test Kafka
./test_kafka_flow.sh
```

## Access Points

- **Kafka Broker**: localhost:9092
- **Kafka UI Dashboard**: http://localhost:8080

## Dashboard Features

- **Topics Management**: Create, view, delete topics
- **Message Browser**: View messages in topics
- **Consumer Groups**: Monitor consumer group status
- **Broker Health**: Cluster and broker metrics
- **Real-time Monitoring**: Live topic and partition stats

## Test

```bash
./test_kafka_flow.sh
```

See CHANGELOG.md for changes.
