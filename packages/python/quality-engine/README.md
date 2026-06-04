# Quality Engine

LLM Observability Quality Engine package.

## Introduction

This service aggregates model evaluation metrics (coherence, faithfulness, toxicity, and perplexity) into a single composite quality score. It implements dynamic weight renormalization to handle missing inputs and triggers console alerts if all sub-metrics are null.

If sub-metrics are not provided directly in the request payload, the quality engine can dynamically fetch them by querying the downstream sub-scorer microservices if they are configured in the environment.

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


