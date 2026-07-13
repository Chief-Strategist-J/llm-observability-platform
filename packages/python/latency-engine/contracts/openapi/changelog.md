# Latency Engine OpenAPI Contract Changelog

## v1.1.0 — 2026-07-13

### Added
- `GET /v1/latency/attribution` — Average latency attribution segment read from Redis
- `AttributionResponse` schema

## v1.0.0 — 2026-06-25

### Added
- `GET /v1/latency/percentiles` — DDSketch quantile read from Redis
- `GET /v1/latency/slo` — multi-window burn rate read from Redis
- `GET /v1/latency/baseline` — historical p99 read from ClickHouse `latency_checkpoints`
- Service-to-service JWT auth (HS256) on all endpoints
- `PercentilesResponse`, `SLOResponse`, `BaselinePoint`, `ErrorResponse` schemas
