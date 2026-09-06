# python-shared

Centralized Python infrastructure package for the LLM Observability Platform, modeled after `packages/node/shared-infra`.

## Modules

- `python_shared.types`: Shared Pydantic base schemas and health response models.
- `python_shared.telemetry`: OpenTelemetry tracer setup & Prometheus metric registries.
- `python_shared.http`: Resilient HTTP client (`httpx`), retries, circuit breakers, FastAPI middlewares.
- `python_shared.db`: Redis connection pool & PostgreSQL helpers (`psycopg`).
- `python_shared.kafka`: `confluent-kafka` producer and consumer factory.
- `python_shared.discovery`: Service catalog registration and resolution.
- `python_shared.feature_flags`: Feature flag evaluation & rule engine helpers.

## Installation

```bash
pip install -e packages/python/python-shared
```
