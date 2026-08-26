# ADR 0005: Fault-Tolerant Asynchronous Messaging Topology and Failure Recovery Architecture

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-EVENT-COST-0005` |
| **Title** | Fault-Tolerant Asynchronous Messaging Topology and Failure Recovery Architecture |
| **Status** | **Accepted** |
| **Date** | 2026-08-26 |
| **Scope** | Kafka Consumer Topology (`event_cost.worker`), Producer SDK (`instrumentation-sdk`), Fault-Tolerance & Crash Recovery (`Kafka`, `Redis`, `SQLite WAL`) |

---

## 1. Context & Problem Statement

High-throughput distributed systems inevitably experience component outages. When client applications emit LLM telemetry via `instrumentation-sdk`, the ingestion engine must guarantee:
1. **Zero Data Loss**: Telemetry span events must never be lost during worker daemon crashes, network partitions, or Kafka broker restarts.
2. **Zero-Latency Application Impact**: Application LLM calls must remain unblocked regardless of worker health or backlog size.
3. **Strict Idempotency**: Re-delivered Kafka messages during consumer recovery must never result in duplicate financial billing or double-counted token usage.
4. **At-Least-Once Delivery**: Kafka offsets must be committed only after downstream persistence has been confirmed.

This ADR defines the fault-tolerant messaging architecture, consumer group topology, crash recovery protocols, and multi-tier failure matrix.

---

## 2. High-Level Design (HLD)

### 2.1 High-Level Producer-Consumer Topology

```mermaid
flowchart TD
    subgraph ProducerSide["1. Producer Layer (Application Runtime)"]
        App["Python App / LLM Service"]
        SDK["instrumentation-sdk Producer"]
        WAL["Local SQLite WAL Buffer (/tmp/llm-obs-wal.db)"]

        App -->|"@llm_observe / llm_span()"| SDK
        SDK -.->|"Kafka Unreachable Fallback"| WAL
    end

    subgraph KafkaBrokerLayer["2. Durable Message Streaming Layer"]
        KafkaBroker["Kafka Broker (Retention: 7 Days)"]
        TopicRaw["Topic: llm.spans.raw"]
        TopicDLQ["Topic: llm.spans.raw.dlq"]

        SDK -->|"Produce JSON Span Events"| TopicRaw
        WAL -.->|"Replay Spans on Reconnect"| TopicRaw
        KafkaBroker --- TopicRaw
        KafkaBroker --- TopicDLQ
    end

    subgraph ConsumerSide["3. Consumer Layer (event-cost Worker)"]
        WorkerDaemon["event-cost Worker Daemon (src/worker/index.py)"]
        ConsumerGroup["Consumer Group: event-cost-worker-group"]
        DedupGuard["Redis Atomic SADD Dedup Guard (dedup:cost_engine)"]
        FenwickEngine["Redis Fenwick & Token Bucket Pipeline"]

        TopicRaw -->|"Poll Batches (batch_size=500)"| ConsumerGroup
        ConsumerGroup --> WorkerDaemon
        WorkerDaemon --> DedupGuard
        DedupGuard -->|"New Span (Return 1)"| FenwickEngine
        WorkerDaemon -.->|"Max Retries Exceeded"| TopicDLQ
    end
```

---

## 3. Low-Level Design (LLD)

### 3.1 Failure & Recovery Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor App as Client Application
    participant SDK as instrumentation-sdk (Producer)
    participant Kafka as Kafka Broker (llm.spans.raw)
    participant Worker as event-cost Worker (Consumer)
    participant Redis as Redis Cache

    Note over App, Kafka: Phase 1: Normal Ingestion Stream
    App->>SDK: LLM Call complete
    SDK->>Kafka: Produce Span Event (Msg #101)

    Note over Worker, Kafka: Phase 2: Worker Daemon Crash / Outage
    Worker--xWorker: Daemon Crash / OOM / Deployment Restart
    SDK->>Kafka: Produce Span Events (Msg #102, #103, #104)
    Note over Kafka: Kafka retains messages #102-#104 safely on disk log

    Note over Worker, Redis: Phase 3: Worker Recovery & Offset Resume
    Worker->>Worker: Restart daemon process
    Worker->>Kafka: Reconnect with group.id 'event-cost-worker-group'
    Kafka-->>Worker: Resume from Last Committed Offset (Msg #101)
    Worker->>Kafka: consumer.consume(num_messages=500)
    Kafka-->>Worker: Return batch containing Msg #102, #103, #104

    loop Per Span in Batch
        Worker->>Redis: SADD dedup:cost_engine span_id
        alt New Span (Return 1)
            Worker->>Redis: Execute 20 Fenwick Tree HINCRBY updates
        else Duplicate Span (Return 0)
            Worker->>Worker: Log duplicate skipped (No-op)
        end
    end

    Worker->>Kafka: consumer.commit(asynchronous=False)
```

---

## 4. Multi-Tier Failure Recovery Matrix

| Outage Scenario | System Behavior | Data Protection Guarantee | Recovery Mechanism |
|---|---|---|---|
| **Worker Crash / Outage** | Kafka retains all incoming messages in `llm.spans.raw` topic on disk log (default 7-day retention). | **Zero Data Loss** | On restart, worker reconnects to `event-cost-worker-group` and resumes polling from the last committed offset. |
| **Worker Crash During Batch Processing** | Offsets are not yet committed because `enable.auto.commit = False`. | **Zero Data Loss** | On worker restart, Kafka re-delivers the batch. The Redis `dedup:cost_engine` set prevents double-counting. |
| **Kafka Broker Outage** | `instrumentation-sdk` fails to publish to Kafka. | **Zero Application Latency / Zero Data Loss** | SDK buffers spans locally in SQLite WAL (`/tmp/llm-obs-wal.db`) and replays them when Kafka connectivity is restored. |
| **Transient Redis Connection Error** | Worker execution raises a network exception during Redis pipeline update. | **At-Least-Once Delivery** | `with_retry` decorator executes 3 retries with exponential backoff (100ms, 200ms, 400ms) before DLQ routing. |
| **Corrupt Payload / Malformed JSON** | Worker fails JSON deserialization. | **Dead-Letter Queue (DLQ) Isolation** | Raw message bytes are routed to `llm.spans.raw.dlq` topic and offset is committed to unblock queue processing. |

---

## 5. Key Technical Implementations

### 5.1 Manual Offset Commit (`src/worker/index.py`)
Auto-commit is explicitly disabled in the worker configuration:

```python
consumer = Consumer({
    "bootstrap.servers": config.kafka_bootstrap_servers,
    "group.id": config.kafka_consumer_group,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,  # Manual commit enforcement
})

# ... Batch processing ...
process_batch(spans, fenwick, bucket, ewma, price_lookup, dedup, metrics)

# Commit offsets ONLY after Redis writes succeed
consumer.commit(asynchronous=False)
```

### 5.2 Atomic Redis Deduplication Lua Guard
To handle re-delivered messages during worker recovery:

```lua
-- DEDUP_CHECK_LUA
local key = KEYS[1]       -- "dedup:cost_engine"
local span_id = ARGV[1]   -- Span UUID
local ttl = tonumber(ARGV[2]) -- 3600 seconds
local added = redis.call('SADD', key, span_id)
if added == 1 then
    redis.call('EXPIRE', key, ttl)
    return 1 -- New span -> proceed to aggregate
end
return 0 -- Duplicate span -> skip
```

---

## 6. End-to-End Call Stack Topology

```text
└── [Worker Lifecycle] src/worker/index.py :: main()
    ├── 1. Initialize confluent_kafka.Consumer(enable.auto.commit=False)
    ├── 2. Subscribe to topic 'llm.spans.raw' (group.id='event-cost-worker-group')
    │
    └── 3. [Polling Loop] _run_consumer_loop()
        ├── 4. Fetch batch: consumer.consume(num_messages=500, timeout=1.0)
        ├── 5. Extract OTel traceparent headers & deserialize JSON payload
        ├── 6. Deduplicate: Redis SADD dedup:cost_engine {span_id}
        ├── 7. Pipeline 20 Fenwick tree updates + Token bucket deductions
        │
        ├── [On Success] consumer.commit(asynchronous=False)
        └── [On Failure] Retry 3x (100ms, 200ms, 400ms) -> Route to DLQ topic 'llm.spans.raw.dlq'
```

---

## 7. Decision Rationale & Consequences

### Positive Consequences
- **High Availability**: Application telemetry emission remains $100\%$ decoupled from worker operational status.
- **Strict Idempotency**: Redis atomic deduplication set guarantees exact financial totals even under repeated consumer crashes.
- **Zero Head-of-Line Blocking**: Unprocessable payloads are safely isolated in DLQ topics without stalling stream ingestion.
