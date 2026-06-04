# Quality Engine

LLM Observability Quality Engine package.

## Introduction

The **Quality Engine** is a core layer-3 service in the LLM Observability Platform. It consumes LLM spans, orchestrates asynchronous quality evaluation, calculates composite quality scores, tracks baseline drifts, and handles real-time quality degradation alerting.

### Core Features & What It Does

1. **Span Ingestion & Pre-flight Checks (F-Q-01)**:
   - Consumes sampled LLM spans from the `llm.spans.sampled` Kafka topic.
   - Evaluates pre-flight skip conditions before kicking off expensive workflows:
     - Skips if `finish_reason` is `content_filter`.
     - Skips if `completion_tokens` is less than 10.
     - Skips if PII is detected.
   - Writes a minimal `skipped` record directly to the database for skipped spans.

2. **Heuristic Prompt Type Detection (F-Q-02)**:
   - Classifies prompt categories using lightweight rules:
     - `code`: If the prompt contains Markdown code blocks (\`\`\`).
     - `rag`: If the span includes a non-null `rag_context` field.
     - `classification`: If the model response is a single word (e.g. classification output).
     - `chat`: Default fallback category.

3. **Response Language Detection (F-Q-03)**:
   - Identifies the language code of the response (e.g. `en`, `es`, `fr`).
   - Flags and logs non-English responses for separate baseline grouping.

4. **Embedding Re-use and Generation (F-Q-04)**:
   - Reuses existing embeddings on the incoming span when present.
   - Automatically calls downstream embedding worker services to generate missing embeddings (500ms timeout guard).

5. **Temporal Workflow Orchestration**:
   - Triggers the Temporal workflow `quality_score_workflow` with deterministic workflow IDs to ensure idempotency.
   - The Temporal workflow coordinates evaluations of coherence, toxicity, faithfulness, and perplexity across downstream microservices.

6. **Composite Quality Score Aggregation (F-Q-06)**:
   - Aggregates sub-scorer metrics.
   - Emits a safety alert to Kafka's `llm.toxicity.flagged` topic if toxicity exceeds `0.75` (F-Q-05).
   - Computes a composite quality score with **dynamic weight renormalization** if any sub-metrics are null (base weights: Coherence=30%, Faithfulness=40%, Toxicity=20%, Perplexity=10%).
   - Asserts mathematical and business invariants (e.g. scores clamped between `[0.0, 1.0]`, alerts if all sub-metrics are null).

7. **Rolling Historical Baselines (F-Q-07)**:
   - Tracks a rolling EWMA (Exponentially Weighted Moving Average) quality baseline per model, endpoint, and prompt-type in Redis.
   - Baseline average window caps at 7 days (10,080 minutes) with an 8-day baseline cache TTL.

8. **Real-time Quality Degradation Alerting (F-Q-08)**:
   - Compares the 1-hour window average score against the historical base quality average.
   - Publishes degradation notifications to the `alerts.quality.degradation` Kafka topic if the average drops below 90% of the baseline (evaluated once 20 samples are collected).
   - Enforces a strict 1-hour rate limit limit per model/endpoint on alerts.


## Business Decision Tree

```
[quality-ST-01 | Request Received]
   |
   +-- [quality-IN-01 | CompositeScoreInput (trace_id, span_id, scores, text attributes)]
       |
       +-- [quality-DC-01 | Pre-calculated scores provided?]
           |-- [yes | Use provided values for coherence, faithfulness, toxicity, perplexity]
           |-- [no  | ScorerClientPort configured?]
           |          |-- [yes | Fetch missing scores dynamically from downstream microservices]
           |          `-- [no  | Retain null for missing scores]
           |
           `-- [quality-PR-01 | Renormalize weights for non-null metrics]
               |   Base weights: coherence=0.30, faithfulness=0.40, toxicity=0.20, perplexity=0.10
               |   normalized_weight = weight / sum(active_weights)
               |
               +-- [quality-DC-02 | Are all active scores null?]
                   |-- [yes | Trigger alert: 'scoring pipeline is broken' (trace_id, span_id)]
                   |          quality_skipped_reason = 'all_scores_null'
                   |          composite_score = null
                   |-- [no  | Calculate composite_score = Σ (normalized_weight * raw_contribution)]
                   |
                   `-- [quality-OUT-01 | Return CompositeScoreResult]
```

## Configuration & Environment Variables

The service can be configured via the following environment variables:

### Database & Cache Settings
| Variable | Description | Default |
| --- | --- | --- |
| `POSTGRES_HOST` | PostgreSQL server hostname | `localhost` |
| `POSTGRES_PORT` | PostgreSQL server port | `5432` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `quality_engine_db` |
| `REDIS_URL` | Redis connection URL for EWMA cache | `redis://localhost:6379/0` |

### Broker & Temporal Settings
| Variable | Description | Default |
| --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated list of Kafka brokers | `localhost:9092` |
| `KAFKA_CONSUMER_GROUP` | Consumer group name for span ingestion | `quality-engine-group` |
| `KAFKA_TOPIC_INPUT` | Kafka topic to consume spans from | `llm.spans.sampled` |
| `TEMPORAL_HOST` | Hostname and port of the Temporal cluster | `localhost:7233` |
| `TEMPORAL_NAMESPACE` | Temporal namespace to trigger workflow in | `default` |
| `TEMPORAL_TASK_QUEUE` | Temporal task queue for quality scoring | `quality-engine-tasks` |

### Downstream Scorer Endpoints
| Variable | Description | Default |
| --- | --- | --- |
| `EMBEDDING_WORKER_URL` | Endpoint of the Embedding Generator service | `http://localhost:8001` |
| `COHERENCE_SERVICE_URL` | Endpoint of the Coherence Scorer service | `http://localhost:8005` |
| `FAITHFULNESS_SERVICE_URL` | Endpoint of the Faithfulness Scorer service | `http://localhost:8006` |
| `TOXICITY_SERVICE_URL` | Endpoint of the Toxicity Scorer service | `http://localhost:8007` |
| `PERPLEXITY_SERVICE_URL` | Endpoint of the Perplexity Scorer service | `http://localhost:8007` |

---

## Running with Docker

### 1. Build the Image
The image is configured to cache dependencies, execute unit and contract tests in-container, and build optimized layers. Build it using:
```bash
docker build -f build/Dockerfile -t chiefj/quality-engine:latest .
```

Alternatively, use the provided deployment helper script which builds, validates, and tags the image with `latest`, `v<version>`, and `stable`:
```bash
./scripts/deploy_docker.sh
```

### 2. Verify and Test Inside the Container
To run the full test suite (including contract and handler unit tests) inside a isolated container instance, run:
```bash
docker run --rm \
  -v "$(pwd)/tests:/app/tests" \
  -e PYTHONPATH=/app/src \
  chiefj/quality-engine:latest pytest /app/tests /app/src/handlers/span_quality/tests -v --tb=short
```

### 3. Apply Database Migrations
Database migrations must be run before starting the worker. Apply them via:
```bash
docker run --rm \
  -e POSTGRES_HOST=your-postgres-host \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=quality_engine_db \
  chiefj/quality-engine:latest ./scripts/migrate.sh
```

### 4. Run the Event Worker Container
To run the Kafka consumer and Temporal trigger daemon container:
```bash
docker run -d \
  --name quality-engine-worker \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e POSTGRES_HOST=postgres \
  -e REDIS_URL=redis://redis:6379/0 \
  -e TEMPORAL_HOST=temporal:7233 \
  -e EMBEDDING_WORKER_URL=http://embedding:8001 \
  chiefj/quality-engine:latest
```

---

## Local Development & Docker Compose

For local development and testing, a multi-container environment with PostgreSQL, Redis, and Kafka can be spun up using Docker Compose:

### Spin up the Dev Stack
```bash
docker compose -f deploy/docker/docker-compose.dev.yaml up -d
```

This starts:
- `postgres` (accessible on `5432`)
- `redis` (accessible on `6379`)
- `zookeeper` and `kafka` (accessible on `9092`)
- `quality-engine` event worker (linked to these services)

### View Logs
```bash
docker compose -f deploy/docker/docker-compose.dev.yaml logs -f quality-engine
```

### Check Container Health
The health status of the worker check endpoint and Kafka broker TCP connectivity is automated via:
```bash
./scripts/health-check.sh
```

---

## Local Unit & Contract Tests
Install dev dependencies locally:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
PYTHONPATH=src pytest -v
```


