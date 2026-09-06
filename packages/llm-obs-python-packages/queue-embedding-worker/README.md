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

| Variable | Default | Description |
|---|---|---|
| `CF_ACCOUNT_ID` | `local-account` | Cloudflare account identifier for Workers AI |
| `CF_API_TOKEN` | - | Cloudflare API Token with Workers AI permissions |
| `EMBEDDING_PROVIDER` | `cloudflare` | Provider adapter key: `cloudflare` / `openai` / `mock` |
| `EMBEDDING_DIMENSIONS` | `1536` | Output dimensions (default for text-embedding-3-small) |
| `DEPLOYMENT_ENV` | `dev` | Tracing attribute value |

### Cloudflare Setup
To use the `cloudflare` provider, you must provide your account credentials:

```bash
docker run -d \
  -e CF_ACCOUNT_ID="your_account_id" \
  -e CF_API_TOKEN="your_api_token" \
  -e EMBEDDING_PROVIDER="cloudflare" \
  chiefj/queue-embedding-worker:latest
```

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

---

## Deployment (Docker)

### Build & Deploy
The worker is fully containerized and pushed to Docker Hub.

```bash
# Set your PAT
export DOCKER_PAT=your_pat

# Run deployment script (builds, tags, and pushes)
bash scripts/deploy_docker.sh
```

### Run Locally (Docker Compose)
Use the development compose file for hot-reloading:

```bash
docker compose -f deploy/docker/docker-compose.dev.yaml up --build
```

The management API will be available at `http://localhost:8002`.

---

## Remote Management API (REST)
The worker now includes a FastAPI management layer (port 8000 in prod).

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | GET | Check worker status and config. |
| `/execute` | POST | Trigger a dry-run job execution. |

### Example Execution
```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "enrich-span",
    "message": {
      "trace_id": "t1",
      "span_id": "s1",
      "model": "text-embedding-3-small",
      "text": "hello world"
    }
  }'
```

---

## Migrations

- Apply strategy is documented in `database/migrations/README.md`.
- Current schema lock is in `database/schema.lock`.
- Migration files include a rollback partner by convention.
