# References: Quality Baseline Worker Architecture \& Design Patterns

This directory contains resources, external documentation references, and architectural templates used during the design and evaluation of the `quality-baseline-worker`.

## External Core Documentation References

### 1. Temporal Orchestration & Schedulers
*   **Documentation:** [Temporal Scheduled Workflows](https://docs.temporal.io/workflows#scheduled-workflow)
*   **Application:** Used to configure the cron schedules for the hourly rolling baseline recomputation and the daily 00:00 UTC quality trend rollup.
*   **Design Pattern:** Persistent workflow scheduling with automatic exponential retries on activity failure.

### 2. ClickHouse Column-Oriented Data Warehousing
*   **Documentation:** [ClickHouse Columnar Aggregation Performance](https://clickhouse.com/docs/en/about-us/performance/)
*   **Application:** Columnar storage choice for yesterday's prompt quality trend aggregates, optimizing long-term analytical queries.
*   **Design Pattern:** Heavy append-only writes via bulk insert blocks.

### 3. Redis Invalidation & Cache-Aside
*   **Documentation:** [Redis Caching Patterns](https://redis.io/docs/manual/client-side-caching/)
*   **Application:** Fast cache key updates `baseline:quality:{model}:{endpoint}:{prompt_type}` to avoid PostgreSQL query loads on the gateway hot-path.
*   **Design Pattern:** Rolling cache overwrite.

### 4. OpenTelemetry Metrics & Telemetry
*   **Documentation:** [OpenTelemetry Metrics Specification](https://opentelemetry.io/docs/specs/otel/metrics/)
*   **Application:** Instrumenting worker execution latencies, Redis write counters, and ClickHouse row tracking gauges.
*   **Design Pattern:** Prometheus exporter adapter mapping.
