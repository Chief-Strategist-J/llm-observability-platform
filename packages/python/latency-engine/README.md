# Latency Engine

The `latency-engine` is a high-performance Kafka consumer worker service that processes raw LLM span events to track and store latency metrics, Service Level Objective (SLO) errors, and latency attribution information in real-time.

---

## 🌲 Business Design Tree

Below is the decision path followed for every span event processed by the latency engine:

```
                          [Raw Span Event Consumed]
                                      │
                                      ▼
               [Validate Span: Has model & latency_ms_total?]
                               /             \
                       (No)   /               \   (Yes)
                             ▼                 ▼
                     [Skip Span]       [Parse UTC Timestamp]
                                               │
           ┌───────────────────────────────────┼──────────────────────────────────┐
           │                                   │                                  │
           ▼                                   ▼                                  ▼
[latency_ms_ttft exists?]             [Is retry_count > 0?]             [SLO threshold check]
      /         \                           /         \                       /         \
(No) /           \ (Yes)             (Yes) /           \ (No)           (Yes)/           \(No)
    ▼             ▼                       ▼             ▼                   ▼             ▼
[Skip]     [Update TTFT Sketch]     [Update Retry]  [Update Total]     [Incr Errors    [Incr Total
           (sketch:ttft:{m}:{h})     (sketch:retry)  (sketch:total)     & Total]        Only]
                  │                                                         │               │
                  ▼                                                         ▼               ▼
           [TPOT Eligible?]                                                 └───────┬───────┘
         (TTFT & Tokens > 0,                                                        │
          Reason != timeout)                                                        │
              /         \                                                           ▼
      (No)   /           \ (Yes)                                           [Attribution tags?]
            ▼             ▼                                                    /          \
         [Skip]     [Calc TPOT]                                         (Yes) /            \ (No)
                    (tpot:latest)                                            ▼              ▼
                                                                     [Store Hash    [Skip]
                                                                      & Agg Avg]
```

---

## 🚀 How to Use the Package

This worker consumes raw LLM span payloads from the `llm.spans.raw` Kafka topic, aggregates latency metrics into DDSketch representations, and persists the serialized sketches to Redis.

### Setup and Installation

1. **Development Environment Setup**
   Using Python 3.11/3.12, install package dependencies in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Environment Variables Config**
   Configure the worker using the following environment variables:
   | Environment Variable | Description | Default |
   |----------------------|-------------|---------|
   | `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers connection string | `localhost:9092` |
   | `KAFKA_CONSUMER_GROUP` | Consumer group for the worker | `latency-engine-cg` |
   | `KAFKA_TOPIC_INPUT` | Kafka topic containing raw span events | `llm.spans.raw` |
   | `REDIS_URL` | Redis URL for stats storage | `redis://localhost:6379/0` |
   | `SLO_CONFIG_PATH` | Path to the SLO threshold YAML configuration | `src/slo_config.yaml` |
   | `HEALTH_PORT` | HTTP port for the `/health` endpoint | `8002` |
   | `SKIP_CONSOLE_EXPORTER` | Skip writing OpenTelemetry traces to stdout | `false` |
   | `SKIP_OTLP_EXPORTER` | Skip exporting traces to an OTLP collector | `true` |

---

## 🛠️ Tracing & Instrumentation

The latency engine has native, high-depth OpenTelemetry tracing built-in:
- **Automatic Context Propagation:** Extracts `traceparent` and `tracestate` from Kafka metadata headers to parent-link spans across network boundaries.
- **Granular Spans:**
  - `latency_handler.handle_spans`: Traces the execution of batch processing.
  - `latency_handler.process_span`: Traces individual span metrics aggregation and includes detailed attributes (`net.dns.latency_ms`, `net.tcp.latency_ms`, `llm.queue.latency_ms`, `llm.inference.latency_ms`) for deep latency attribution.

---

## 🐳 Docker Deployment & Testing

We provide a production-ready, multi-stage build setup to construct lightweight runtime images and execute self-tests.

### 1. Build Docker Image
Build the Docker image locally. This triggers internal unit tests automatically:
```bash
docker build -t latency-engine:latest -f build/Dockerfile .
```

### 2. Deploy via Docker Compose
To boot up the complete pipeline (Kafka/Redpanda, Redis, and the Latency Engine worker):
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```

### 3. Verification & Live Testing
To verify the engine is alive and healthy:
```bash
./scripts/health-check.sh
```
Or execute unit tests inside the package:
```bash
./scripts/test.sh
```
