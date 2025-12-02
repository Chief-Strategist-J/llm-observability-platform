# Kafka Messaging Pipeline

Complete Kafka messaging implementation with producer, consumer, admin, and transactional support.

## Architecture

```
infrastructure/orchestrator/kafka/
├── clients/
│   ├── kafka_producer_client.py       - Producer with batching, compression, idempotence
│   ├── kafka_consumer_client.py       - Consumer with group coordination, offset management
│   ├── kafka_consumer_group_client.py - Consumer group management
│   ├── kafka_admin_client.py          - Topic/partition/config management
│   └── kafka_transaction_client.py    - Exactly-once transaction support
└── utils/
    ├── serializers.py                 - String, JSON, Bytes, Integer serializers
    ├── partition_selector.py          - Hash, RoundRobin, Sticky partitioning
    └── compression.py                 - GZIP, Snappy, LZ4, ZSTD compression
```

## Features

### Kafka UI
- Official `provectuslabs/kafka-ui` image
- Web-based interface for Kafka cluster management
- Topic browsing and message inspection
- Consumer group monitoring
- Cluster health visualization
- Traefik integration with SSL/TLS
- Accessible at `https://kafka-ui-0.localhost` or `http://scaibu.kafka-ui`

### Producer
- Message serialization (String, JSON, Bytes, Integer)
- Partition selection (Hash/Murmur2, RoundRobin, Sticky)
- Batch accumulation and compression
- Idempotent producer with sequence numbers
- Async send with futures and callbacks
- Retry logic with exponential backoff
- Configurable acks (0, 1, all)

### Consumer
- Consumer group coordination
- Partition assignment strategies (Range, RoundRobin)
- Offset management (auto-commit, manual commit, sync/async)
- Message deserialization
- Rebalancing support with listeners
- Heartbeat management
- Seek operations (beginning, end, offset)

### Admin
- Topic create/delete/list/describe
- Partition management
- Configuration updates (topic, broker)
- Consumer group operations
- Metadata fetching

### Transactions
- Begin/commit/abort transaction lifecycle
- Send messages in transaction
- Offset commit in transaction
- Exactly-once semantics
- State management

## Usage

### Producer

```python
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import (
    KafkaProducerClient, ProducerConfig, ProducerRecord
)

config = ProducerConfig(
    bootstrap_servers=["localhost:9092"],
    client_id="my-producer",
    acks="all",
    enable_idempotence=True
)

producer = KafkaProducerClient(config)

record = ProducerRecord(
    topic="my-topic",
    value="Hello Kafka",
    key="my-key"
)

future = producer.send(record)
metadata = future.get(timeout=30)

print(f"Message sent to partition {metadata.partition} at offset {metadata.offset}")

producer.close()
```

### Consumer

```python
from infrastructure.orchestrator.kafka.clients.kafka_consumer_client import (
    KafkaConsumerClient, ConsumerConfig
)

config = ConsumerConfig(
    bootstrap_servers=["localhost:9092"],
    group_id="my-group",
    auto_offset_reset="earliest"
)

consumer = KafkaConsumerClient(config)
consumer.subscribe(["my-topic"])

records = consumer.poll(timeout_ms=1000)

for record in records:
    print(f"Consumed: {record.value} from partition {record.partition}")

consumer.commit()
consumer.close()
```

### Transactions

```python
from infrastructure.orchestrator.kafka.clients.kafka_transaction_client import (
    KafkaTransactionClient, TransactionalConfig
)
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import ProducerRecord

config = TransactionalConfig(transactional_id="my-transaction")
client = KafkaTransactionClient(config)

client.begin_transaction()

try:
    record = ProducerRecord(topic="my-topic", value="transactional message")
    client.send(record)
    
    client.commit_transaction()
except Exception as e:
    client.abort_transaction()
    raise

client.close()
```

## Workflows

### Producer Workflow
```python
params = {
    "messages": [
        {"topic": "test-topic", "value": "message-1", "key": "key-1"},
        {"topic": "test-topic", "value": "message-2", "key": "key-2"}
    ],
    "bootstrap_servers": ["localhost:9092"],
    "flush": True
}
```

### Consumer Workflow
```python
params = {
    "group_id": "my-group",
    "topics": ["test-topic"],
    "bootstrap_servers": ["localhost:9092"],
    "poll_count": 5,
    "timeout_ms": 1000
}
```

### Topic Management Workflow
```python
params = {
    "operation": "create",
    "topic_name": "new-topic",
    "num_partitions": 3,
    "replication_factor": 1,
    "bootstrap_servers": ["localhost:9092"]
}
```

### End-to-End Workflow
```python
params = {
    "topic_name": "e2e-test",
    "test_messages_count": 100,
    "num_partitions": 3,
    "instance_id": 0,
    "cleanup": True
}
```

## Activities

### Producer Activities
- `send_message_activity` - Send single message
- `send_batch_activity` - Send message batch
- `flush_producer_activity` - Flush pending messages
- `close_producer_activity` - Close producer

### Consumer Activities
- `poll_messages_activity` - Poll messages from topics
- `commit_offsets_activity` - Commit consumer offsets
- `seek_offset_activity` - Seek to specific offset
- `close_consumer_activity` - Close consumer

### Topic Activities
- `create_topic_activity` - Create new topic
- `delete_topic_activity` - Delete topics
- `list_topics_activity` - List all topics
- `describe_topic_activity` - Get topic metadata
- `list_consumer_groups_activity` - List consumer groups
- `describe_consumer_group_activity` - Describe consumer group

### Transaction Activities
- `begin_transaction_activity` - Start transaction
- `send_transactional_message_activity` - Send in transaction
- `commit_transaction_activity` - Commit transaction
- `abort_transaction_activity` - Abort transaction
- `close_transaction_client_activity` - Close transaction client

## Worker

Start the Kafka messaging worker:

```bash
python infrastructure/orchestrator/workers/kafka_messaging_worker.py
```

The worker listens on queue `kafka-messaging-queue` and processes all Kafka workflows and activities.

## Testing

Run the complete test suite:

```bash
pytest infrastructure/tests/units/kafka_tests/ -v
```

Run specific test modules:

```bash
pytest infrastructure/tests/units/kafka_tests/test_kafka_producer.py -v
pytest infrastructure/tests/units/kafka_tests/test_kafka_consumer.py -v
pytest infrastructure/tests/units/kafka_tests/test_kafka_admin.py -v
pytest infrastructure/tests/units/kafka_tests/test_kafka_transactions.py -v
pytest infrastructure/tests/units/kafka_tests/test_kafka_compression.py -v
pytest infrastructure/tests/units/kafka_tests/test_kafka_integration.py -v
```

## Port Configuration

Kafka ports are managed via `port_registry.yaml`:

```yaml
kafka:
  broker_port: 9092
  controller_port: 19093
  instance_increment: 100
  max_instances: 10
```

For instance 0: broker=9092, controller=19093  
For instance 1: broker=9192, controller=19193  
And so on...

## Logging

All components use LogQL structured logging:

```
event=producer_send topic=my-topic partition=0 offset=42 duration_ms=15 trace_id=abc-123
event=consumer_poll messages_count=10 duration_ms=250 trace_id=def-456
event=activity_complete activity=send_message duration_ms=20 trace_id=ghi-789
```

## Algorithm Implementation

This implementation follows the complete Kafka algorithm architecture:

- **Producer**: Serialization → Metadata fetch → Partition selection → Batch accumulation → Compression → Send
- **Consumer**: Subscribe → Join group → Partition assignment → Poll → Deserialize → Offset commit
- **Replication**: Leader-follower protocol, ISR management, high-watermark tracking
- **Transactions**: Init → Begin → Send → Commit/Abort with exactly-once guarantees

---

## 🚀 Quick Start - Running Tests

### Step 1: Start Temporal Server
```bash
temporal server start-dev
```

### Step 2: Start Kafka Services (Docker)
```bash
cd /home/j/live/dinesh/llm-chatbot-python

# Start Kafka broker
docker-compose -f infrastructure/orchestrator/config/docker/kafka-dynamic-docker.yaml up -d

# Start Kafka UI (optional but recommended)
docker-compose -f infrastructure/orchestrator/config/docker/kafka-ui-dynamic-docker.yaml up -d

# Verify services are running
docker ps | grep kafka
```

### Step 3: Start Kafka Messaging Worker
```bash
# Terminal 1
source .venv/bin/activate
cd /home/j/live/dinesh/llm-chatbot-python

python infrastructure/orchestrator/workers/kafka_messaging_worker.py
```

### Step 4: Trigger E2E Test
```bash
# Terminal 2
source .venv/bin/activate
cd /home/j/live/dinesh/llm-chatbot-python

python infrastructure/orchestrator/trigger/common/kafka_e2e_test_start.py
```

**Expected Output:**
- ✅ Topic created with 3 partitions
- ✅ 10 messages produced and consumed
- ✅ Consumer group coordination working
- ✅ Offsets committed successfully
- ✅ Topic cleanup (if enabled)

### Step 5: View Results in Kafka UI
Open `http://localhost:8080` or `http://scaibu.kafka-ui`

---

## Dependencies


```bash
pip install kafka-python pytest
```

Optional compression libraries:

```bash
pip install python-snappy lz4 zstandard
```
