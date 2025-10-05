# Kafka Infrastructure

Lightweight Kafka setup for event-driven architecture development.

## Quick Start

```bash
# Start Kafka only
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka up -d

# Start with services that need Kafka
docker-compose -f infrastructure/kafka/docker-compose.kafka.yml --profile kafka \
  -f service/kg-service/docker-compose.yml up -d
```

## Access Points

- **Kafka Broker**: localhost:9092
- **Default Topics**: Automatically created as needed

## Environment Variables

- `KAFKA_SUBNET`: Kafka network subnet (default: 172.29.0.0/16)

## Usage Examples

### Create a Topic
```bash
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic my-topic
```

### Produce Messages
```bash
docker exec kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic my-topic
```

### Consume Messages
```bash
docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic my-topic --from-beginning
```

## Scaling Later

This setup uses KRaft mode for simplicity. To scale to multiple nodes:

1. Add more broker services to docker-compose.kafka.yml
2. Update KAFKA_CONTROLLER_QUORUM_VOTERS
3. Adjust replication factors

See Apache Kafka documentation for multi-node setup.

## Features

- **KRaft Mode**: No Zookeeper dependency, faster startup
- **Lightweight**: Single node for development
- **Scalable**: Easy to expand to multiple brokers
- **Conditional**: Only runs when explicitly requested

See CHANGELOG.md for detailed changes.
