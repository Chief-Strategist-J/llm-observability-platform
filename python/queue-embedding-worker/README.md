# queue-embedding-worker

A contract-driven queue worker for `enrich-span` jobs with pluggable embedding providers (`cloudflare`, `openai`, `mock`), schema consistency checks, and migration scaffolding.

## What this service does

- Validates and registers jobs from `contracts/jobs/enrich-span.yaml` during startup.
- Processes `enrich-span` payloads into deterministic embedding metadata.
- Resolves embedding provider via config (`EMBEDDING_PROVIDER`) using a provider port + adapter pattern.
- Exposes in-process helper API functions (`health`, `execute`) for local tests and dry-runs.

---

## Architecture (high-level)

```text
API/Queue input
   -> worker.index.handle_job
      -> worker.registry (contract + handler validation)
         -> features.enrich_span.service
            -> shared.di.providers (provider resolution)
               -> infra.clients.<provider>
                  -> normalized result
```

## Runtime decision flow

```text
Client / Queue Event
        |
        v
+-----------------------+
| api.execute(...)      |  (or direct worker.handle_job)
+-----------------------+
        |
        | opens span: "api.execute"
        v
+-----------------------+
| worker.handle_job     |
+-----------------------+
        |
        | load_config(env)
        |  - dimensions
        |  - embedding_provider
        |
        | opens span: "queue.consume"
        v
+-----------------------+
| JOB_REGISTRY lookup   |
+-----------------------+
        |
        | if job missing -> KeyError("Unknown job ...")
        v
+-------------------------------+
| registry built at import-time |
+-------------------------------+
        |
        | load + validate contract
        | validate handler signature
        v
+-----------------------+
| job.handler(...)      |
| enrich_span(...)      |
+-----------------------+
        |
        | validate payload/dataclass
        | validate dimensions > 0
        | validate text non-empty
        v
+-------------------------------+
| resolve_embedding_provider()  |
+-------------------------------+
   |            |             |
 cloudflare    openai        mock
   |            |             |
   +------------+-------------+
                |
                v
+-------------------------------------------+
| provider.create_embedding(request, dims)  |
+-------------------------------------------+
                |
                v
+-------------------------------------------+
| return normalized result                  |
+-------------------------------------------+
```

---

## Directory map

- `contracts/` — YAML job contract + OpenAPI + GraphQL + Proto schemas.
- `src/worker/` — config, registry, queue entrypoint.
- `src/features/enrich_span/` — feature-level orchestration.
- `src/infra/clients/` — provider-specific adapters.
- `src/shared/` — ports, DI, errors, tracing, utils.
- `database/migrations/` — SQL migrations and rollback.
- `tests/` — unit, integration, and contract consistency tests.
- `scripts/` — local run/test/migrate/health scripts.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CF_ACCOUNT_ID` | `local-account` | Cloudflare account identifier for deployment context |
| `CF_QUEUE_NAME` | `span-enrichment` | Queue name consumed by worker |
| `EMBEDDING_DIMENSIONS` | `1536` | Output dimensions metadata |
| `WORKER_CONCURRENCY` | `5` | Max concurrent worker slots |
| `WORKER_RATE_LIMIT_PER_SEC` | `50` | Rate guardrail |
| `WORKER_BACKOFF_MS` | `500` | Retry backoff metadata |
| `EMBEDDING_PROVIDER` | `cloudflare` | Provider adapter key: `cloudflare` / `openai` / `mock` |
| `DEPLOYMENT_ENV` | `dev` | Tracing attribute value |

---

## Local usage

### 1) Run tests

```bash
cd python/queue-embedding-worker
bash scripts/test.sh
```

`scripts/test.sh` validates the contract first, then runs `pytest`.

### 2) Health check

```bash
cd python/queue-embedding-worker
bash scripts/health-check.sh
```

### 3) Run local dry-run entrypoint

```bash
cd python/queue-embedding-worker
bash scripts/run.sh
```

---

## API examples (documentation samples)

> Note: This project currently provides in-process API helpers (`src/api/index.py`), not an HTTP server binary. The curl examples below are reference payload/response examples for future HTTP gateway wiring.

### Health (example)

```bash
curl -s http://localhost:8080/health
```

```json
{
  "status": "ok",
  "queue": "span-enrichment",
  "concurrency": 5,
  "rate_limit_per_sec": 50
}
```

### Execute enrich-span (example)

```bash
curl -s -X POST http://localhost:8080/execute/enrich-span \
  -H 'content-type: application/json' \
  -d '{
    "trace_id": "trace-1",
    "span_id": "span-1",
    "model": "text-embedding-3-small",
    "text": "payment failed for order #123"
  }'
```

```json
{
  "status": "processed",
  "job": "enrich-span",
  "result": {
    "trace_id": "trace-1",
    "span_id": "span-1",
    "embedding_key": "emb_1234567890abcdef123456",
    "dimensions": 1536,
    "model": "text-embedding-3-small",
    "provider": "cloudflare"
  }
}
```

---

## Contracts

`enrich-span` contract is maintained in multiple forms and checked for consistency by tests:

- YAML: `contracts/jobs/enrich-span.yaml`
- OpenAPI: `contracts/api.yaml`
- GraphQL: `contracts/graphql/schema.graphql`
- Proto: `contracts/proto/enrich_span.proto`

Use tests in `tests/contracts/` to catch schema drift.

---

## Docker

### Build

```bash
cd python/queue-embedding-worker
docker build -t queue-embedding-worker:local .
```

### Run with compose

```bash
cd python/queue-embedding-worker
docker compose up --build
```

---

## Migrations

- Apply strategy is documented in `database/migrations/README.md`.
- Current schema lock is in `database/schema.lock`.
- Migration files include a rollback partner by convention.
