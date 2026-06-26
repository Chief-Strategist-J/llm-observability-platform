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
   | `JWT_SECRET` | Secret key for verifying incoming HS256 service JWTs | — |

### 🌐 REST Query API Endpoints

The service exposes HTTP query endpoints on port `8002` (configurable via `HEALTH_PORT`). Except for `/health`, all endpoints require service-to-service JWT authentication in the `Authorization: Bearer <token>` header, signed with `JWT_SECRET`.

#### 1. Query Latency Percentiles
Retrieve the `p50`, `p95`, and `p99` latency values computed from the DDSketch in Redis.
* **Path**: `GET /v1/latency/percentiles`
* **Query Parameters**:
  * `model` (required, e.g. `gpt-4`)
  * `hour_of_day` (required, integer `0-23`)
  * `quantiles` (optional, comma-separated floats, default: `0.50,0.95,0.99`)
* **Example curl**:
  ```bash
  curl -H "Authorization: Bearer <JWT_TOKEN>" \
    "http://localhost:8002/v1/latency/percentiles?model=gpt-4&hour_of_day=14"
  ```

#### 2. Query SLO Burn Rates
Retrieve the 1-hour, 6-hour, and 3-day budget burn rates along with the remaining error budget percentage.
* **Path**: `GET /v1/latency/slo`
* **Query Parameters**:
  * `model` (required)
  * `endpoint` (required)
* **Example curl**:
  ```bash
  curl -H "Authorization: Bearer <JWT_TOKEN>" \
    "http://localhost:8002/v1/latency/slo?model=gpt-4&endpoint=/v1/chat/completions"
  ```

#### 3. Query Historical Baseline
Retrieve daily `p99` TTFT and total latency over the past N days from ClickHouse.
* **Path**: `GET /v1/latency/baseline`
* **Query Parameters**:
  * `model` (required)
  * `hour_of_day` (required, `0-23`)
  * `days` (optional, integer `1-90`, default: `7`)
* **Example curl**:
  ```bash
  curl -H "Authorization: Bearer <JWT_TOKEN>" \
    "http://localhost:8002/v1/latency/baseline?model=gpt-4&hour_of_day=14&days=7"
  ```

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
