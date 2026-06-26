# ADR-011: Implement FastAPI service-to-service REST Query API for latency-engine

* **Status**: Accepted
* **Date**: 2026-06-26
* **Deciders**: Jaydeep, Antigravity

## Context and Problem Statement
How can upstream systems and observability dashboards query calculated percentiles, SLO burn rates, and historical baselines from latency-engine securely and performantly?

## Decision Drivers
* **D1**: Access to metrics must be secured via service-to-service authentication.
* **D2**: Telemetry query processing must not block worker's CPU-bound Kafka polling loop.
* **D3**: API responses must strictly conform to the OpenAPI v1 contract specs.
* **D4**: ClickHouse connection outages must not prevent HTTP server startup.

## Options Considered
* **Option A**: FastAPI app running on a background thread within the consumer process.
* **Option B**: Independent query service deployment.

## Pros and Cons of Options

### Option A: FastAPI app running on a background thread within the consumer process
* **Good**: Reuses existing exposed HTTP port (`8002`), doesn't block the Kafka consumer loop because it runs in a separate thread.
* **Good**: Leverages FastAPI for parameter validation, dependency injection, and JWT verification.
* **Bad**: CPU resource contention if request rates scale past limits.

### Option B: Independent query service deployment
* **Good**: Complete process isolation between consumer loop and API readers.
* **Bad**: Increases container deployment footprint, requires additional network management and configuration.

## Decision Outcome
**Chosen**: Option A (FastAPI app running via uvicorn in a daemon thread).
* **Rationale**: Reuses the existing port setup, keeps the deployment footprint lightweight, and meets all performance, security, and contract constraints.

## Failure Modes Created

### FM-1: Port conflicts on port 8002
* **Symptom**: Service fail-starts with port already in use.
* **Detection**: Startup logs contain port binding error.
* **Prevention**: HTTP port is fully configurable via `HEALTH_PORT` environment variable.

## Review Trigger
* Review if HTTP query volume exceeds 10,000 requests/second (at that point, Option B becomes necessary).
