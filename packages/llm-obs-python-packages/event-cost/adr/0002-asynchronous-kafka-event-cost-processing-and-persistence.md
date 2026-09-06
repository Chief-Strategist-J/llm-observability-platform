# ADR 0002: Asynchronous Kafka Event Cost Worker Processing and Persistence Pipeline

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-EVENT-COST-0002` |
| **Title** | Asynchronous Kafka Event Cost Worker Processing and Persistence Pipeline |
| **Status** | **Accepted** |
| **Date** | 2026-08-25 |
| **Scope** | Asynchronous Worker (`event_cost.worker`), Kafka Consumer (`llm.spans.raw`), Redis Fenwick & Token Bucket Aggregation (`event_cost.handlers`) |

---

## 1. Context & Problem Statement

High-volume production environments process thousands of LLM spans per second. Synchronous database writes during span ingestion introduce severe latency overhead to client application LLM calls. 

`event_cost.worker` decouples telemetry ingestion from application runtime by:
1. Consuming span events asynchronously from Kafka topic `llm.spans.raw` in batch groups.
2. Evaluating micro-USD costs and price version compliance via domain handlers (`event_cost.handlers.llm_spans_raw`).
3. Aggregating spend across 5 dimensions and 4 time windows in Redis Fenwick Trees and executing retroactive token bucket deductions.

---

## 2. High-Level Design (HLD)

### 2.1 High-Level Architecture Topology

```mermaid
flowchart TD
    subgraph IngestionStream["1. Telemetry Ingestion Stream"]
        SDKApi["instrumentation-sdk REST API / Kafka Producer"]
        KafkaTopic["Kafka Broker Topic\n(llm.spans.raw)"]
        SDKApi --> KafkaTopic
    end

    subgraph WorkerService["2. Event Cost Worker Processing Service"]
        KafkaConsumer["KafkaConsumer Group (event-cost-worker-group)"]
        BatchBuffer["Batch Ingestion Buffer (batch_size=500, poll_timeout=1.0s)"]
        CostCalculator["event_cost.handlers Domain Handler"]
        RetryMechanism["Dead-Letter Queue (DLQ) & Exponential Retry"]

        KafkaTopic --> KafkaConsumer
        KafkaConsumer --> BatchBuffer
        BatchBuffer --> CostCalculator
        CostCalculator -.->|On Exception| RetryMechanism
    end

    subgraph AnalyticalStores["3. Persistent Analytical Data Stores"]
        RedisFenwick[("Redis Fenwick Trees\n(fenwick:{dim}:{win}:{key})")]
        RedisTokenBucket[("Redis Token Buckets\n(budget:tb:{org}:{proj})")]

        CostCalculator --> RedisFenwick
        CostCalculator --> RedisTokenBucket
    end
```

### 2.2 Three-Plane Architectural Blueprint (Control, Data & Messaging)

```mermaid
flowchart TD
    subgraph ControlPlane["1. CONTROL PLANE (Worker Management & Configuration)"]
        WorkerRegistry["worker-registry.yaml"]
        FeatureConfig["feature-registry.yaml"]
        ModelVersionConfig["model_price_versions.yaml"]
        HealthCheckEndpoint["HTTP Health Probe (:8001/health)"]
    end

    subgraph DataPlane["2. DATA PLANE (Batch Processing & Redis Aggregation)"]
        SpanParser["Span JSON Deserializer & Validator"]
        CostReconciler["Price Version Reconciliation & Anomaly Detection"]
        FenwickWriter["Redis Pipeline Fenwick Tree Aggregator"]
        TokenBucketWriter["Token Bucket Deficit Deductor"]

        SpanParser --> CostReconciler
        CostReconciler --> FenwickWriter
        CostReconciler --> TokenBucketWriter
    end

    subgraph MessagingPlane["3. MESSAGING PLANE (Kafka Consumer Group & Offsets)"]
        ConsumerGroup["Kafka Consumer Group (event-cost-worker-group)"]
        OffsetCommit["Manual Batch Offset Committer (commit_sync)"]
        DlqTopic["Kafka DLQ Topic (llm.spans.raw.dlq)"]

        ConsumerGroup --> OffsetCommit
        OffsetCommit -.->|Processing Error| DlqTopic
    end

    ControlPlane --> DataPlane
    MessagingPlane --> DataPlane
```

---

## 3. Low-Level Design (LLD)

### 3.1 Sequence Diagram: Kafka Batch Ingestion & Redis Aggregation

```mermaid
sequenceDiagram
    autonumber
    actor Kafka as Kafka Broker (llm.spans.raw)
    participant Worker as event_cost.worker.index Daemon
    participant Handler as event_cost.handlers.llm_spans_raw
    participant Redis as Redis Cache

    loop Background Consumption Loop
        Kafka->>Worker: Poll batch of messages (e.g. 500 span records)
        activate Worker
        
        Worker->>Worker: Deserialize JSON & extract OTel traceparent header

        loop Per Span in Batch
            Worker->>Handler: process_span(span, fenwick, bucket, ewma, price_lookup, dedup)
            activate Handler
            Handler->>Redis: Atomic SADD dedup:cost_engine span_id
            alt Span is New
                Handler->>Redis: Pipeline HINCRBY 20 Fenwick tree updates (5 dims x 4 windows)
                Handler->>Redis: Token bucket deduction for overshoot tokens
            end
            deactivate Handler
        end

        Worker->>Kafka: Commit Kafka Offsets (asynchronous=False)
        deactivate Worker
    end
```

### 3.2 Key Worker Call Contract (`src/event_cost/worker/index.py`)

```python
import logging
from event_cost.handlers.llm_spans_raw.index import process_batch
from event_cost.worker.config import load_config
from event_cost.worker.registry import build_registry

logger = logging.getLogger(__name__)

def main() -> None:
    config = load_config()
    redis_client = redis_lib.from_url(config.redis_url)
    ...
    build_registry(
        batch_handler=lambda spans: process_batch(
            spans, fenwick, bucket, ewma, price_lookup, dedup, metrics
        )
    )
    ...
```

---

## 4. End-to-End Call Stack Topology

```text
└── [Daemon Startup] event_cost/src/event_cost/worker/index.py :: main()
    ├── 1. Read configuration via event_cost.worker.config :: load_config()
    ├── 2. Initialize Redis adapters (RedisFenwickAdapter, RedisTokenBucketAdapter, RedisDedupAdapter)
    ├── 3. Initialize YamlPriceLookupAdapter(config.price_config_path) & PrometheusAdapter
    │
    └── 4. [Kafka Loop] event_cost/src/event_cost/worker/index.py :: _run_consumer_loop()
        ├── 5. consumer.consume(num_messages=500, timeout=1.0)
        │
        ├── 6. event_cost/src/event_cost/handlers/llm_spans_raw/index.py :: process_batch()
        │   ├── 7. Check idempotency: dedup.is_new(span_id)
        │   ├── 8. Build 20 Fenwick updates: handler.build_fenwick_updates(span)
        │   ├── 9. Pipeline updates to Redis: fenwick.pipeline_update(updates)
        │   ├── 10. Reconcile price version & log burn ratio against EWMA
        │   └── 11. Deduct token bucket overshoot if applicable
        │
        └── 12. consumer.commit(asynchronous=False) -> Acknowledge Kafka message batch
```

---

## 5. Decision Rationale & Consequences

### Positive Consequences
- **Asynchronous Execution**: Ingestion latency is $0\text{ms}$ on client application LLM calls since database writes run out-of-band in worker daemons.
- **Bulk Aggregation Throughput**: Redis pipelines execute 20 Fenwick updates per span concurrently without blocking worker execution.
- **Kafka Offset Safety**: `consumer.commit(asynchronous=False)` is only executed after Redis writes succeed or failed items are pushed to DLQ.
