# Toxicity Service — High-Level Design (HLD) & Low-Level Design (LLD)

| Field | Value |
|---|---|
| **Package** | `packages/python/toxicity` |
| **Version** | `0.2.0` |
| **Architecture Pattern** | Hexagonal Architecture (Ports & Adapters) + Clean Domain-Driven Design |
| **Status** | Production-Ready (Merged Single Package) |

---

## 1. High-Level Design (HLD)

### 1.1 System Context & Macro Topology

The **Toxicity Service** is the multi-label NLP safety classification engine in the LLM Observability Platform. It classifies generated texts across 6 toxicity categories (`toxicity`, `severe_toxicity`, `obscene`, `threat`, `insult`, `identity_hate`) using an ONNX-optimized `unitary/toxic-bert` model on CPU.

It serves two operational modalities:
1. **Stateless Scoring Engine (Worker Mode)**: Synchronous high-throughput REST API called by trace enrichment engines and evaluation pipelines.
2. **Safety Event Publisher (Orchestrator Mode)**: Automatically emits flagged toxic payloads to Kafka (`llm.toxicity.flagged`) when toxicity threshold is breached.

```mermaid
flowchart TD
    subgraph Clients["CALLERS & INGESTION"]
        EnrichmentSvc["Trace / Span Enrichment Service"]
        EvalWorker["Evaluation / LLM Judge Worker"]
        RestCaller["External API Consumers"]
    end

    subgraph ToxicityPackage["packages/python/toxicity (Port :8008)"]
        direction TB
        subgraph API["REST & Ingress Plane"]
            FastAPI["FastAPI HTTP Server"]
            HealthHandler["/healthz Handler"]
            ScoreHandler["/score Handler"]
            MetricsHandler["/metrics (Prometheus)"]
        end

        subgraph Domain["Core Domain Layer"]
            Service["score_toxicity() Service"]
            Rules["Toxicity Rules Engine\n(Threshold > 0.50)"]
            DualPass["Dual-Pass Chunking Strategy\n(Max-of-Two Passes)"]
        end

        subgraph Infra["Infra & Adapters Layer"]
            OnnxAdapter["DetoxifyOnnxAdapter\n(optimum ONNX CPU Runtime)"]
            KafkaAdapter["KafkaToxicityPublisherAdapter\n(confluent-kafka Producer)"]
            OtelTracer["OpenTelemetry Tracer\n(toxicity TracerProvider)"]
        end
    end

    subgraph PlatformInfra["PLATFORM INFRASTRUCTURE (llmobs-network)"]
        KafkaBroker["Kafka Broker :9092\nTopic: llm.toxicity.flagged"]
        OtelCol["OTEL Collector :4317/:4318"]
        TempoStore["Grafana Tempo (Traces)"]
        Prometheus["Prometheus / Grafana (Metrics)"]
    end

    Clients -->|POST /score\nJSON or W3C Headers| FastAPI
    FastAPI --> ScoreHandler
    ScoreHandler --> Service
    Service --> Rules
    Service --> DualPass
    DualPass -->|Tokenize & Score| OnnxAdapter
    Service -->|Publish Flagged| KafkaAdapter
    Service -->|Span Context| OtelTracer

    KafkaAdapter -->|JSON Event Key: trace_id| KafkaBroker
    OtelTracer -->|OTLP gRPC| OtelCol
    OtelCol --> TempoStore
    Prometheus -->|Scrape /metrics| FastAPI
```

---

### 1.2 Multi-Plane Architectural Topology

```mermaid
flowchart LR
    subgraph ControlPlane["1. CONTROL & LIFECYCLE PLANE"]
        Env["Environment Matrix\n(TOXICITY_MODEL_ID, KAFKA_BOOTSTRAP_SERVERS)"]
        Lifespan["FastAPI Lifespan Context Manager"]
        Warmup["Eager Model & Tokenizer Warmup"]
        Env --> Lifespan --> Warmup
    end

    subgraph DataPlane["2. INFERENCE & DATA PLANE"]
        TokenStream["Raw Response Text Stream"]
        Tokenizer["AutoTokenizer (toxic-bert)"]
        OrtModel["ORTModelForSequenceClassification (ONNX CPU)"]
        Sigmoid["Sigmoid Multi-Label Probs"]
        
        TokenStream --> Tokenizer --> OrtModel --> Sigmoid
    end

    subgraph MessagingPlane["3. MESSAGING & TELEMETRY PLANE"]
        OtelSpans["OTel Span: toxicity.score"]
        KafkaEmit["Kafka Topic: llm.toxicity.flagged"]
        PromMetrics["Prometheus HTTP Metrics"]
    end

    ControlPlane -.-> DataPlane
    DataPlane --> MessagingPlane
```

---

### 1.3 End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Client as Upstream Caller
    participant Handler as API Handler (/score)
    participant Svc as Core Domain Service
    participant Adapter as DetoxifyOnnxAdapter
    participant Model as ONNX Runtime (CPU)
    participant Rules as Rules Engine
    participant Kafka as Kafka Publisher
    participant OTel as OpenTelemetry / Tempo

    Client->>Handler: POST /score {text, trace_id?, span_id?}
    Handler->>OTel: Extract W3C traceparent or body trace/span IDs
    Handler->>Svc: score_toxicity(input, scorer, trace_id, span_id, publisher)
    
    activate Svc
    Svc->>OTel: Start span "toxicity.score"
    Svc->>Adapter: tokenize(text)
    Adapter-->>Svc: token_ids (length = N)

    alt N <= 510 tokens (Single Pass)
        Svc->>Adapter: score_token_ids(token_ids)
        Adapter->>Model: Run inference graph with [CLS] + tokens + [SEP]
        Model-->>Adapter: Logits -> Sigmoid probabilities
        Adapter-->>Svc: ToxicityScores
    else N > 510 tokens (Dual-Pass Strategy)
        Svc->>Adapter: score_token_ids(first 510)
        Adapter->>Model: Inference pass 1
        Model-->>Adapter: Scores 1
        Svc->>Adapter: score_token_ids(last 510)
        Adapter->>Model: Inference pass 2
        Model-->>Adapter: Scores 2
        Svc->>Svc: Combine: max(Scores 1, Scores 2) per label
        Note over Svc: strategy = "max_of_two_passes"
    end

    Svc->>Rules: is_flagged(toxicity_score > 0.50)
    Rules-->>Svc: flagged (bool), flag ("TOXIC_RESPONSE" | None)

    opt If flagged == True AND publisher is configured
        Svc->>Kafka: publish_flagged(trace_id, span_id, score, scores)
        Kafka->>Kafka: Produce & flush to 'llm.toxicity.flagged'
    end

    Svc->>OTel: End span (attributes: output.score, flagged, strategy)
    Svc-->>Handler: ToxicityResult
    deactivate Svc

    Handler-->>Client: 200 OK (ScoreResponse JSON)
```

---

## 2. Low-Level Design (LLD)

### 2.1 Hexagonal Layer Boundaries & File Inventory

```
packages/python/toxicity/
├── src/
│   ├── core/domain/                     # PURE DOMAIN LAYER (Zero 3rd-party framework deps)
│   │   ├── ports/
│   │   │   ├── toxicity_scorer_port.py    # Inbound / Outbound Scorer Protocol
│   │   │   └── toxicity_publisher_port.py # Outbound Event Publisher Protocol
│   │   ├── rules.py                       # Business rules, thresholds, flag constants
│   │   ├── service.py                     # Primary domain orchestration service
│   │   └── types.py                       # Domain value objects & dataclasses
│   ├── infra/adapters/                  # INFRASTRUCTURE LAYER
│   │   ├── detoxify_onnx_adapter.py       # ONNX Runtime model adapter & warmup
│   │   └── kafka_publisher_adapter.py     # Confluent-Kafka producer adapter
│   ├── api/rest/v1/                     # INGRESS / INTERACTION LAYER
│   │   ├── app.py                         # FastAPI application factory & lifespan
│   │   ├── router.py                      # Router aggregator
│   │   └── handlers/
│   │       ├── health.py                  # Liveness & readiness probes
│   │       └── score.py                   # Toxicity evaluation handler
│   └── shared/tracing/                  # CROSS-CUTTING CONCERNS
│       └── tracer.py                      # OpenTelemetry tracing helper
```

---

### 2.2 Domain Data Contracts & Types (`core/domain/types.py`)

```python
@dataclass(frozen=True)
class ToxicityInput:
    text: str

@dataclass(frozen=True)
class ToxicityScores:
    toxicity: float          # General toxicity probability [0.0, 1.0]
    severe_toxicity: float   # Highly aggressive / hateful content
    obscene: float           # Vulgarity / profanity
    threat: float            # Physical harm or intimidation
    insult: float            # Disparaging or derogatory language
    identity_hate: float     # Hate speech targeted at protected groups

@dataclass(frozen=True)
class ToxicityResult:
    scores: ToxicityScores
    long_response_strategy: str | None = None  # None or "max_of_two_passes"
    score: float | None = None                 # Primary score (same as scores.toxicity)
    flagged: bool = False                      # True if score > 0.50
    flag: str | None = None                    # "TOXIC_RESPONSE" or None
    skipped: bool = False                      # True if pipeline failure caught gracefully
    skip_reason: str | None = None             # "pipeline_failure" or None
```

---

### 2.3 Port Protocols (`core/domain/ports/`)

#### Scorer Port:
```python
class ToxicityScorerPort(Protocol):
    def tokenize(self, text: str) -> list[int]:
        """Convert raw input text into model-specific integer token IDs."""
        ...

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        """Run forward model inference against token sequence and return multi-label probabilities."""
        ...
```

#### Publisher Port:
```python
class ToxicityPublisherPort(Protocol):
    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        """Publish flagged toxic span event to message broker."""
        ...
```

---

### 2.4 Mathematical Dual-Pass Formulation

For an arbitrary token sequence $T = [t_1, t_2, \dots, t_N]$:

$$\text{Scores}(T) = 
\begin{cases} 
f_{\text{ONNX}}(T) & \text{if } N \le 510 \\
\max\Big(f_{\text{ONNX}}(T[1:510]),\; f_{\text{ONNX}}(T[N-509:N])\Big) & \text{if } N > 510 
\end{cases}$$

Where:
- $f_{\text{ONNX}}(S) = \sigma(\mathbf{W} \cdot \text{Encoder}([CLS] \oplus S \oplus [SEP]) + \mathbf{b})$
- $\max(\mathbf{u}, \mathbf{v})_i = \max(u_i, v_i)$ element-wise $\forall i \in \{1, \dots, 6\}$

This guarantees that toxic prefixes or toxic suffixes in long generations are never masked by safe intermediate text.

---

### 2.5 Failure Modes & Circuit Breakers

| Failure Scenario | Component | Detection | Mitigation & Behavior |
|---|---|---|---|
| **Tokenizer / Model Crash** | `DetoxifyOnnxAdapter` | Unhandled `Exception` in inference | Caught by `service.py`; records exception on OTel span; returns `skipped=True, skip_reason="pipeline_failure"`; API returns `200 OK` with neutral scores to prevent cascading upstream failures. |
| **Kafka Broker Down** | `KafkaToxicityPublisherAdapter` | `KafkaException` or timeout on `flush()` | Publisher is non-blocking with local buffer; errors are logged without breaking `/score` HTTP response. |
| **Cold Container Latency** | `FastAPI Lifespan` | Slow first request | Eager `warmup()` runs dummy inference on container start before health check reports ready. |
| **Missing Kafka Configuration** | `app.py` | `KAFKA_BOOTSTRAP_SERVERS` is empty/unset | Adapter initializes with `bootstrap_servers=None` and behaves as a silent no-op (Worker Mode). |

---

### 2.6 Observability & Metric Telemetry

- **OpenTelemetry Span**: `toxicity.score`
  - Attributes: `input.length`, `output.score`, `output.flagged`, `output.strategy`, `skipped`, `skip_reason`.
  - Context Propagation: Extracts W3C `traceparent` or custom header/body IDs.
- **Prometheus Metrics** (`/metrics` endpoint via `prometheus-client`):
  - HTTP request duration, status codes, request count.
