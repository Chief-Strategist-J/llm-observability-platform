# ADR 0004: Consolidated Kafka Messaging Infrastructure, Middleware Pipeline Architecture, and CQRS Event Stream

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-SDK-0004` |
| **Title** | Consolidated Kafka Messaging Infrastructure, Middleware Pipeline Architecture, and CQRS Event Stream |
| **Status** | **Accepted** |
| **Date** | 2026-08-26 |
| **Scope** | `src/infra/messaging/` (`broker`, `producer`, `consumer`, `middleware`, `topics`, `migrations`, `reporters`, `tracing`), W3C Context Propagation, DLQ Routing, CQRS Projections, and Package Structure Policy |

---

## 1. Context & Problem Statement

1. **Decentralized Messaging Components**: Previously, Kafka connection creation, producer/consumer factories, and topic configuration were scattered across separate modules, risking connection pool leaks and uncoordinated broker settings.
2. **Lack of Standardized Middleware Pipelines**: Outbound event publishes and inbound message processing lacked unified resilience decorators (tracing, circuit breaking, deadline retries, idempotency deduplication, DLQ error routing, worker concurrency limits, and rebalance heartbeats).
3. **DRY Architecture Enforcement**: Features needed a centralized, pre-built messaging engine so that no individual feature duplicates broker configuration, serialization, or error handling.

---

## 2. Decision & Architecture Overview

1. **Consolidated Messaging Hierarchy (`src/infra/messaging/`)**:
   - **`broker/`**: `KafkaBrokerConfig` singleton managing bootstrap servers, SASL/SSL credentials, acks, linger, compression, and retries.
   - **`producer/`**: Thread-safe `KafkaProducerFactory` (singleton connection pool) and `KafkaProducerClient`.
   - **`consumer/`**: `KafkaConsumerFactory`, `KafkaConsumerClient`, `SpanConsumerHandler`, and `CQRS` append-only projections & query selectors (`consumer/cqrs/`).
   - **`middleware/`**: Generic, language-agnostic pipeline execution engine (`pipeline.py`, `producer_middleware.py`, `consumer_middleware.py`, `tracing_middleware.py`).
   - **`topics/`**: Declarative topic provisioner (`topic_provisioner.py`) and central manager (`topic_manager.py`).
   - **`migrations/`**: Topic schema and partition migration manager (`kafka_topic_migration.py`).
   - **`reporters/`**: `KafkaSpanReporter` for telemetry span exporting.
   - **`tracing/`**: `MessagingTracer` for W3C `traceparent` context injection/extraction and OpenTelemetry `PRODUCER`/`CONSUMER` spans.

2. **Producer & Consumer Middleware Execution Engine**:
   - **Producer Chain**: `with_tracing_producer` $\rightarrow$ `with_circuit_breaker_producer` $\rightarrow$ `with_retry_producer` $\rightarrow$ `with_idempotence_guard` $\rightarrow$ `with_schema_validation` $\rightarrow$ `with_serialization` $\rightarrow$ `with_partition_key_selection`.
   - **Consumer Chain**: `with_dlq_on_failure` $\rightarrow$ `with_tracing_consumer` $\rightarrow$ `with_heartbeat_during_processing` $\rightarrow$ `with_concurrency_limit` $\rightarrow$ `with_tenant_context` $\rightarrow$ `with_retry_count_header` $\rightarrow$ `with_deserialization` $\rightarrow$ Domain Handler Execution.

3. **Policy Alignment**:
   - Updated universal package structure policy in `policies/rules/folderStructure/package-structure.md` with Core Rule #2 (DRY Guardrail) enforcing zero code repetition across messaging components.

---

## 3. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph AppDomain["Application / SDK Domain Layer"]
        App["Event Producers & Span Handlers"]
    end

    subgraph MessagingEngine["src/infra/messaging/ Engine"]
        subgraph ProducerPipeline["Producer Pipeline"]
            P_Trace["with_tracing_producer"]
            P_CB["with_circuit_breaker_producer"]
            P_Retry["with_retry_producer"]
            P_Dedupe["with_idempotence_guard"]
            P_Schema["with_schema_validation"]
            P_Codec["with_serialization"]
            P_Key["with_partition_key_selection"]
            
            P_Trace --> P_CB --> P_Retry --> P_Dedupe --> P_Schema --> P_Codec --> P_Key
        end

        subgraph ConsumerPipeline["Consumer Pipeline"]
            C_DLQ["with_dlq_on_failure"]
            C_Trace["with_tracing_consumer"]
            C_Heartbeat["with_heartbeat_during_processing"]
            C_Sem["with_concurrency_limit"]
            C_Tenant["with_tenant_context"]
            C_RetryCount["with_retry_count_header"]
            C_Codec["with_deserialization"]
            
            C_DLQ --> C_Trace --> C_Heartbeat --> C_Sem --> C_Tenant --> C_RetryCount --> C_Codec
        end

        subgraph ConnectionPools["Connection Pool & Topic Management"]
            ProdFactory["KafkaProducerFactory"]
            ConsFactory["KafkaConsumerFactory"]
            TopicManager["TopicManager & Migrations"]
        end
    end

    subgraph KafkaBroker["Apache Kafka Infrastructure"]
        Topics[("Topics: llm.spans.raw, llm.spans.dlq")]
    end

    App -->|Publish Event| P_Trace
    P_Key --> ProdFactory
    ProdFactory -->|Kafka Protocol| Topics

    Topics -->|Consume Records| ConsFactory
    ConsFactory --> C_DLQ
    C_Codec -->|Execute Handler| App
```

---

## 4. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Service as Ingestion Service
    participant Pipe as ProducerMiddlewarePipeline
    participant Factory as KafkaProducerFactory
    participant Kafka as Kafka Broker
    participant ConsFactory as KafkaConsumerFactory
    participant ConsPipe as ConsumerMiddlewarePipeline
    participant Handler as SpanConsumerHandler

    Service->>Pipe: execute(ProduceCtx)
    Pipe->>Pipe: Start OTEL PRODUCER Span and Inject W3C Headers
    Pipe->>Pipe: Check Topic Circuit Breaker State
    Pipe->>Pipe: Validate Idempotency Key and Serialize Payload
    Pipe->>Factory: get_producer()
    Factory->>Kafka: Send RecordMetadata to Topic
    Kafka-->>Factory: Acknowledge Offset
    Factory-->>Pipe: Success

    Kafka->>ConsFactory: Fetch Record Batch
    ConsFactory->>ConsPipe: execute(ConsumeCtx)
    ConsPipe->>ConsPipe: Start OTEL CONSUMER Span from W3C Headers
    ConsPipe->>ConsPipe: Acquire Concurrency Semaphore
    ConsPipe->>ConsPipe: Start Background Heartbeat Loop
    ConsPipe->>Handler: handle_span(ConsumeCtx)
    Handler-->>ConsPipe: Processing Complete
    ConsPipe-->>ConsFactory: Commit Watermark Offset
```

---

## 5. Verification Results

- **Unit Tests**: Passed 100% in `tests/unit/infra/messaging/test_messaging_middleware.py`.
- **Pipeline Integrity**: Verified circuit breaker trip recovery, DLQ routing on poison payloads, and W3C traceparent propagation.
