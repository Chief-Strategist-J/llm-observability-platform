# Changelog

All notable changes to the `latency-baseline-worker` will be documented in this file.

## [1.0.0] - 2026-06-23

### Added
- **Core Scheduler & Registry:** Registered `LatencyBaselineWorkflow` and `hourly_checkpoint` activity in [latency-baseline-worker.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/registry/workers/latency-baseline-worker.yaml).
- **Hourly DDSketch Checkpoints (F-L-11):** Completed Redis DDSketch retrieval, quantile extraction (p50, p95, p99), and ClickHouse `latency_checkpoints` table insert.
- **TTFT Regression Check (F-L-12):** ClickHouse historical median baseline computing with cold-start suppression (< 7 points) and Kafka alert production.
- **Sketch Rotation health logs (F-L-13):** Current and prior hour key check in Redis, producing `sketch_missing_total` log on outage.
- **Docker operations:** Created [Dockerfile](file:///home/btpl-lap-22/live/llm-observability-platform/packages/python/latency-baseline-worker/build/Dockerfile) and multi-container [docker-compose.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/python/latency-baseline-worker/deploy/docker/docker-compose.yaml) configs with non-conflicting port maps.
- **CI pipeline:** Created GitHub workflow [.github/workflows/latency-baseline-worker-test.yml](file:///home/btpl-lap-22/live/llm-observability-platform/.github/workflows/latency-baseline-worker-test.yml).
