# Kafka (Single-node) with Docker + Kafka UI

Minimal, fast, and reliable local Kafka with dual listeners for host and Docker clients, plus a concise test suite.

## Quick Start

```bash
cd infrastructure/kafka

# Start broker (host listener on 29092) and UI
docker-compose -f docker-compose.kafka.yml --profile kafka up -d
docker-compose -f docker-compose.kafka-ui.yml --profile kafka-ui up -d

# Run tests (producer, consumer, partitions, large message)
python3 test_kafka.py

# Open UI
xdg-open http://localhost:8080 2>/dev/null || echo "Open http://localhost:8080"
```

## Endpoints

- Kafka (host): `localhost:29092`
- Kafka (docker network): `kafka:9092`
- Kafka UI: `http://localhost:8080`

## Compose Highlights

- Dual listeners: internal `PLAINTEXT_INTERNAL://kafka:9092`, external `PLAINTEXT_EXTERNAL://localhost:29092`
- KRaft single-node: broker+controller, voter `1@kafka:9093`
- Message limits raised to 10 MB; socket buffer 100 MB
- Faster consumer startup: `KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0`
- Persistent volume `kafka-data`

## Useful Commands

```bash
# List topics (inside broker)
docker exec kafka /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Create topic
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 1

# Console producer/consumer (inside broker)
docker exec -it kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic my-topic
docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic my-topic --from-beginning --max-messages 10

# Logs
docker logs kafka
docker logs kafka-ui

# Stop
docker-compose -f docker-compose.kafka-ui.yml --profile kafka-ui down
docker-compose -f docker-compose.kafka.yml --profile kafka down
```

## Notes

- Python tests default to `localhost:29092` and cover connection, topic ops, producer/consumer, partitions, and 5MB message end-to-end.
- Kafka UI connects via Docker network using `kafka:9092` and should show brokers/topics.

## Troubleshooting

```bash
# Verify broker
docker ps | grep kafka
docker exec kafka sh -c 'nc -z localhost 9092'

# Network
docker network inspect kafka_kafka-network | jq '.[0].Containers' 2>/dev/null || true

# Reset (destructive)
docker-compose -f docker-compose.kafka.yml --profile kafka down -v && \
docker-compose -f docker-compose.kafka.yml --profile kafka up -d
```