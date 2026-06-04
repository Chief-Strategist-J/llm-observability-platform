# ADR-003 — Quality Baseline and Trend Rollup Worker

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 003                                                               |
| **Date**    | 2026-06-04                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/quality-baseline-worker`                          |

---

## Context

The LLM Observability Platform requires computing rolling average quality scores and tracking historical quality degradation metrics. Specifically:
1. **F-Q-09 (Rolling Baseline Recomputation)**: Hourly calculation of the 7-day average baseline quality score for combinations of `model`, `endpoint`, and `prompt_type` in PostgreSQL (`quality_scores`), caching the results in Redis (`baseline:quality:{model}:{endpoint}:{prompt_type}`) to prevent database-intensive queries during hot paths.
2. **F-Q-10 (Quality Trend Rollup)**: Daily rollup at 00:00 UTC summarizing yesterday's average scores, flag frequencies, and volume metrics, appending them into a columnar ClickHouse database (`quality_trend`) for historical reporting and dashboards.

To ensure consistency, resilience, and horizontal scalability, these periodic executions are designed using Temporal scheduled workflows running in a dedicated worker.

### Driving Forces
- Avoid database-intensive queries (like averaging PostgreSQL tables) during hot-path scoring requests.
- Decouple multi-database operations (PostgreSQL, ClickHouse, Redis) from application business logic.
- Ensure consistent scheduling, automatic retries, and manual trigger controls.
- Prevent container startup crashes and import path mismatches in packaging.

---

## Decision

Implement the `quality-baseline-worker` as a dedicated Python package combining a FastAPI health checker and a Temporal workflow runtime. 

1. **Hexagonal Architecture Isolation**: Decouple database interactions by defining clear ports (`PostgresPort`, `RedisPort`, `ClickHousePort`, `MetricsPort`) and implementing concrete adapters under `src/infra/adapters/`.
2. **Explicit PYTHONPATH settings**: Added `ENV PYTHONPATH=/app/src` inside [Dockerfile](file:///home/btpl-lap-22/live/obs/packages/python/quality-baseline-worker/build/Dockerfile) to allow python to resolve namespace sub-packages (`api`, `shared`, `infra`, `features`, `worker`) without requiring explicit package setup or `__init__.py` files.
3. **Auto-Deployment scripting**: Configured [deploy_docker.sh](file:///home/btpl-lap-22/live/obs/packages/python/quality-baseline-worker/scripts/deploy_docker.sh) to push builds directly to Docker Hub.

---

## Failure-First System Building (FFSB) Analysis

Applying the platform's brutal failure-first framework (`ffsb.md`), we identify the following key failure modes:

### Mode 1: clickhouse-down (ClickHouse Unavailability)
- **Symptom**: Daily trend rollup fails with connection exceptions.
- **Trigger**: ClickHouse is down during the daily 00:00 UTC rollup.
- **Recovery/Prevention**:
  - Alert on Temporal dashboard when the `RollupQualityTrend` workflow fails.
  - Settle alert triggers using Prometheus metric `temporal_workflow_failed`.
  - Temporal automatically retries the failed activities with exponential backoff.
  - If ClickHouse downtime exceeds Temporal's retry limits, operators run the workflow manually via Temporal UI once the database is restored.

### Mode 2: redis-down (Cache Write Failure)
- **Symptom**: Baseline cache overwrites fail. Upstream evaluators read stale baseline values from their fallback layers.
- **Trigger**: Redis is down or overloaded during the hourly recomputation write.
- **Recovery/Prevention**:
  - Implement write retries with backoff in the worker's `write_redis_baselines` activity.
  - Configure upstream evaluation services to fall back gracefully to a hardcoded default or the last known good baseline if the Redis key is missing.

### Mode 3: temporal-connection-failure (Orchestration Outage)
- **Symptom**: The worker container crashes immediately on startup or enters a LoopBackOff state.
- **Trigger**: Temporal service host (port 7233) is unreachable on startup.
- **Recovery/Prevention**:
  - Ensure the `quality-temporal` container is verified healthy by using Docker Compose `depends_on` conditions.
  - Ensure connection attempts loop and retry rather than immediately terminating the container if a transient network partition exists.

### Mode 4: pythonpath-missing (Import Error Crash)
- **Symptom**: The container starts but terminates instantly with `ModuleNotFoundError: No module named 'api'`.
- **Trigger**: Setuptools does not find packages without `__init__.py` files, and `PYTHONPATH` is missing from the environment.
- **Recovery/Prevention**:
  - Rigidly configure `ENV PYTHONPATH=/app/src` in the production [Dockerfile](file:///home/btpl-lap-22/live/obs/packages/python/quality-baseline-worker/build/Dockerfile) to guarantee clean import paths.

---

## Consequences

### Positive
- **Fast Hot-Paths**: Upstream scorers query Redis instead of running expensive PG aggregates, keeping latency low.
- **Microservices Compliance**: Adheres to the platform's Hexagonal Architecture and Worker registry guidelines.
- **Strong Portability**: Easy to replace databases/caches because of the isolated adapter layers.

### Negative / Trade-offs
- **Temporal Dependency**: The pipeline relies completely on a functioning Temporal server.
- **Multi-Database Consistency**: Requires managing states in PostgreSQL, Redis, and ClickHouse concurrently.
- **Reversal Cost**: High. Replacing Temporal workflows would require rewriting schedulers and cron states in celery or raw cron jobs.

---

## Alternatives Considered

- **Option A: Pure Celery Cron Workers**
  - *Elimination Reason*: Celery lacks fine-grained workflow visibility, activity retry control, and state management compared to Temporal.
- **Option B: Run Postgres aggregates on scoring request**
  - *Elimination Reason*: Running dynamic `avg()` queries across large PostgreSQL tables on hot paths violates the platform's latency goals.
