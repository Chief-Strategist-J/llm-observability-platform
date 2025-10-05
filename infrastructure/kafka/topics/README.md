# Topic Definitions and Management

## Predefined Topics

- `user.requests` - User queries and requests
- `kg.enhancements` - Knowledge graph enhancements
- `rag.updates` - RAG search results
- `workflow.events` - Automation workflow triggers

## Topic Creation Scripts

Run these to create topics:

```bash
# Create all standard topics
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic user.requests --partitions 3 --replication-factor 1
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic kg.enhancements --partitions 3 --replication-factor 1
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic rag.updates --partitions 3 --replication-factor 1
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic workflow.events --partitions 3 --replication-factor 1
```
