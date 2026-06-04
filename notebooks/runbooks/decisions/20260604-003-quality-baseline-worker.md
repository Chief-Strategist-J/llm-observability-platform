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

### Mode 1: Slow Not Down (PostgreSQL Lock Contention)
- **Symptom**: Ingestion services experience thread-pool starvation, causing timeout cascades, while health check probes remain green.
- **Trigger**: Upstream scorers query PostgreSQL aggregates synchronously under heavy concurrent load. 
- **Recovery/Prevention**:
  - Offload calculations to the background using Temporal scheduled crons.
  - Upstream scorers perform $O(1)$ reads from the Redis cache in sub-millisecond times, keeping the request loop fast.

### Mode 2: Correct Response, Wrong Data (Unvalidated Cache / DB Synchronization Drift)
- **Symptom**: Evaluator computes quality deviations against outdated or corrupt rolling baseline scores, leading to false negatives on degradation metrics.
- **Trigger**: The worker fails to update Redis due to connection failures, or writes incorrect data type structures.
- **Recovery/Prevention**:
  - Implement strict schema validations on Redis baseline values.
  - Implement read-through fallbacks in the scorer: if a Redis baseline key is missing, default back to the last known baseline or default threshold rather than failing silently.

### Mode 3: Works Until Specific Conditions (OOM Termination & Startup Crash)
- **Symptom**: The container crashes instantly with `OOMKilled` or `ModuleNotFoundError` on startup.
- **Trigger**: Worker package imports fail due to missing `PYTHONPATH` context on container start.
- **Recovery/Prevention**:
  - Set `ENV PYTHONPATH=/app/src` inside the production Dockerfile to guarantee python resolves directories.
  - Implement container health check conditions in docker-compose configs.

### Mode 4: Cascading Failure (Temporal Orchestration / Worker Outage)
- **Symptom**: Historical aggregations stop and Grafana metric databases go stale, but the core system does not throw errors.
- **Trigger**: The Temporal server goes offline or network partition separates the worker from Temporal port 7233.
- **Recovery/Prevention**:
  - Configure Grafana dashboards to verify timestamps of incoming data: if aggregate data is older than 24 hours, show banner alerts.
  - Persistent Temporal workflow retries buffer the tasks until connection is restored.

### Mode 5: Configuration Drift (Temporal Namespace or Port Registry Misalignment)
- **Symptom**: The worker starts up but never runs workflows, or routes traffic to incorrect environments.
- **Trigger**: Environment namespace or port mappings are edited in local configurations without a proper code deployment.
- **Recovery/Prevention**:
  - Enforce configuration as code: all environment variables (Temporal task queues, ports) must be pinned in version control.
  - Startup sanity checks validate variables before starting the worker.

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
