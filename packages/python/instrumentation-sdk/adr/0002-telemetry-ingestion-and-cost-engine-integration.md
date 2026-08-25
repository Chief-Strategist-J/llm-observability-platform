# ADR 0002: Telemetry Ingestion Pipeline and Event Cost Engine Integration

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-SDK-0002` |
| **Title** | Telemetry Ingestion Pipeline and Event Cost Engine Integration |
| **Status** | **Accepted** |
| **Date** | 2026-08-25 |
| **Scope** | Telemetry SDK (`instrumentation-sdk`), Cost Engine (`event-cost`), Worker (`event-cost-worker`) |

---

## 1. Context & Problem Statement

The Python Instrumentation SDK (`instrumentation-sdk`) captures real-time LLM telemetry (prompt/completion tokens, latency, TTFT, PII flags, and model parameters). To support downstream billing, budget tracking, and real-time dashboard analytics (e.g. in Next.js `web-app`), `instrumentation-sdk` must interface seamlessly with:
- **`event-cost`**: The standalone micro-USD cost engine and pricing registry.
- **`event-cost-worker`**: The high-throughput asynchronous Kafka streaming worker.
- **PostgreSQL / ClickHouse**: The persistent analytical data store.

This ADR defines the High-Level Design (HLD) and Low-Level Design (LLD) for span ingestion, cost computation, offline WAL resilience, and REST API retrieval endpoints.

---

## 2. High-Level Design (HLD)

### 2.1 High-Level Architecture Topology

```mermaid
flowchart TD
    subgraph CaptureLayer["1. In-App Capture & SDK Instrumentation"]
        ClientApp["Python / LLM Application"]
        AutoInst["init_auto_instrumentation()\n(Patches OpenAI, Anthropic, LiteLLM, LangChain)"]
        ContextMgr["llm_span() Context Manager / @llm_observe"]
        
        ClientApp --> AutoInst
        ClientApp --> ContextMgr
    end

    subgraph SDKCore["2. Instrumentation SDK Core Pipeline"]
        PIIScanner["Inline PII & Injection Scanner\n(Aho-Corasick Trie)"]
        Sampler["Deterministic Sampler\n(SHA256(span_id) % 100 == 0)"]
        CostLookup["event-cost Price Lookup\n(model_prices.yaml)"]
        ReliableReporter["Reliable Kafka / WAL Reporter\n(In-Memory Queue + Local SQLite WAL Fallback)"]

        AutoInst --> PIIScanner
        ContextMgr --> PIIScanner
        PIIScanner --> Sampler
        Sampler --> CostLookup
        CostLookup --> ReliableReporter
    end

    subgraph DeliveryStorage["3. Delivery & Analytical Storage Layer"]
        RestAPI["FastAPI Ingestion Server\n(POST /v1/spans, GET /v1/metrics/prices)"]
        KafkaBroker["Kafka Broker\n(Topic: llm.spans.raw)"]
        CostWorker["event-cost-worker\n(Consumes spans & computes micro-USD)"]
        AnalyticsDB[("PostgreSQL / ClickHouse / Redis\n(Spans, Traces, Cost Ledgers)")]

        ReliableReporter -->|Online: HTTP POST /v1/spans| RestAPI
        ReliableReporter -.->|Offline: Write to WAL| ReliableReporter
        RestAPI --> KafkaBroker
        KafkaBroker --> CostWorker
        CostWorker --> AnalyticsDB
    end

    subgraph Consumers["4. Dashboard Consumers"]
        WebApp["Next.js Web App (:3000)"]
        Grafana["Grafana & Tempo Portal (:3002)"]

        WebApp -->|Fetch REST API / Server DB Query| RestAPI
        Grafana -->|Query Datasource| AnalyticsDB
    end
```

### 2.2 Core Responsibilities

| Subsystem Component | Primary Responsibility | Data Input | Data Output |
|---|---|---|---|
| **`instrumentation-sdk`** | Capture LLM telemetry, scan PII, compute tokens & TTFT | Client LLM API calls | `LLMSpanContext` / JSON Span Payload |
| **`event-cost`** | Evaluate exact micro-USD costs from pricing tables | Model, Provider, Tokens | Cost in micro-USD (`cost_usd_micro`) |
| **`ReliableReporter`** | Enqueue spans, fallback to local SQLite WAL on network drop | JSON Span Payload | HTTP Post / Kafka Event / SQLite WAL Record |
| **`event-cost-worker`** | Process Kafka span streams & persist to PostgreSQL/ClickHouse | `llm.spans.raw` Kafka topic | Partitioned database records & cost ledgers |

---

## 3. Low-Level Design (LLD)

### 3.1 Sequence Diagram: Span Ingestion & Cost Processing Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor LLMApp as Client LLM Application
    participant SDK as instrumentation-sdk Core
    participant CostEngine as event-cost Engine
    participant WAL as Local SQLite WAL
    participant RestAPI as FastAPI Ingestion Server (8000)
    participant Kafka as Kafka Broker (llm.spans.raw)
    participant Worker as event-cost-worker
    participant DB as PostgreSQL Analytics DB

    LLMApp->>SDK: Execute LLM Call (e.g. gpt-4o, 150 prompt / 200 comp tokens)
    activate SDK
    SDK->>SDK: scan_prompt(text) [Aho-Corasick PII Check]
    SDK->>SDK: count_tokens(prompt, model) [Tiktoken Count]
    
    SDK->>CostEngine: calculate_cost("gpt-4o", 150, 200)
    activate CostEngine
    CostEngine-->>SDK: cost_usd_micro = 1750 ($0.00175 USD)
    deactivate CostEngine

    Note over SDK, RestAPI: Phase 2: Reliable Telemetry Reporting
    SDK->>RestAPI: POST /v1/spans (JSON Span Payload)
    
    alt REST API Online (HTTP 200)
        RestAPI->>Kafka: Produce message to topic 'llm.spans.raw'
        RestAPI-->>SDK: 200 OK (Span Received)
    else REST API Offline / Network Outage
        SDK->>WAL: Write record to /tmp/llm-obs-wal.db
        Note over SDK, WAL: Background retry loop replays WAL when connection recovers
    end
    deactivate SDK

    Note over Kafka, DB: Phase 3: Asynchronous Worker Consumption
    Kafka->>Worker: Consume span batch from 'llm.spans.raw'
    activate Worker
    Worker->>Worker: Aggregate costs by org_id, project_id, service_name
    Worker->>DB: INSERT INTO llm_spans_partitioned (trace_id, span_id, cost_usd_micro...)
    DB-->>Worker: Commit Success
    deactivate Worker
```

### 3.2 Key Function Signatures & Data Contracts

#### Span Ingestion Request Schema (`api/rest/v1/schemas/spans.py`)
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class SpanIngestRequest(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd_micro: int
    duration_ms: float
    ttft_ms: Optional[float] = None
    pii_detected: bool = False
    injection_attempt: bool = False
    metadata: Optional[Dict[str, Any]] = None
```

#### Cost Calculation Contract (`event_cost/service.py`)
```python
def calculate_cost(
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int
) -> int:
    """
    Calculates LLM execution cost in micro-USD (1 USD = 1,000,000 micro-USD).
    """
    price_config = get_model_price(model=model, provider=provider)
    input_cost = (prompt_tokens / 1_000_000.0) * price_config.input_price_per_1m
    output_cost = (completion_tokens / 1_000_000.0) * price_config.output_price_per_1m
    return int(round((input_cost + output_cost) * 1_000_000))
```

---

## 4. Decision Rationale & Consequences

### Positive Consequences
- **Zero Latency Impact on User App**: LLM span capture and cost calculations occur asynchronously in non-blocking background tasks (`asyncio.create_task`) or reliable WAL buffers.
- **Offline Resilience**: If the ingestion API or database goes down, client applications continue running without interruption, buffering spans safely in SQLite WAL storage until connections recover.
- **Unified Price Registry**: `model_prices.yaml` serves as the single source of truth for both `instrumentation-sdk` and `event-cost`, supporting hot-reloading via `POST /v1/metrics/prices/reload`.

### Negative Consequences
- Operating Kafka and worker containers requires additional infrastructure orchestration in production.
