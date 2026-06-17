# LLM Observability Platform: Feature-Wise Queries

This directory contains standardized query configuration files (`queries.yaml`) organized feature-by-feature. Each file documents critical diagnostics across five dimensions: TraceQL, LogQL, PostgreSQL, PromQL, and Kafka/Redis commands.

## Directory Structure
* [span_ingestion_preflight/](file:///home/btpl-lap-22/live/obs/queries/span_ingestion_preflight/queries.yaml) - Input spans, skip filters, and DLQ tracking.
* [prompt_type_detection/](file:///home/btpl-lap-22/live/obs/queries/prompt_type_detection/queries.yaml) - Classification and language mappers.
* [composite_score_computation/](file:///home/btpl-lap-22/live/obs/queries/composite_score_computation/queries.yaml) - Metrics computations and embedding caching.
* [quality_baseline_update/](file:///home/btpl-lap-22/live/obs/queries/quality_baseline_update/queries.yaml) - Redis baseline cache entries.
* [degradation_alerting/](file:///home/btpl-lap-22/live/obs/queries/degradation_alerting/queries.yaml) - Average evaluation thresholds and notifications.
* [human_review/](file:///home/btpl-lap-22/live/obs/queries/human_review/queries.yaml) - Pending reviews queue and SLO status.
* [system_diagnostics/](file:///home/btpl-lap-22/live/obs/queries/system_diagnostics/queries.yaml) - Host and container-level CLI diagnostics (find, grep, git, ps, docker inspect, jq, ss, netstat, lsof, tcpdump, strace, journalctl, awk, sed).

---

## Query Types and Execution Guide

### 1. TraceQL Queries
* **Used for**: Querying trace hierarchies and tracking latency bottlenecks in Tempo.
* **How to run**: 
  1. Open Grafana (`http://localhost:3002`).
  2. Go to **Explore** and select the **Tempo** (Traces) datasource.
  3. Change the query type to **TraceQL**, paste the query string (e.g. `{resource.service.name="quality-engine"}`), and run query.

### 2. LogQL Queries
* **Used for**: Searching container and API log streams in Loki.
* **How to run**:
  1. Open Grafana (`http://localhost:3002`).
  2. Go to **Explore** and select the **Loki** (Logs) datasource.
  3. Paste the LogQL query string into the query builder.

### 3. PromQL Queries
* **Used for**: Fetching system and quality metric graphs in Prometheus.
* **How to run**:
  1. Open the Prometheus UI (`http://localhost:9090`).
  2. Enter the PromQL query string in the search bar and press **Execute** (or select the **Prometheus** datasource in Grafana Explore).

### 4. PostgreSQL Queries
* **Used for**: Analyzing persistent quality scores and reviews stored in the database.
* **How to run**:
  ```bash
  docker exec -it quality-engine-postgres psql -U postgres -d quality_engine_db -c "SELECT * FROM quality_scores LIMIT 10;"
  ```

### 5. Kafka Console Queries
* **Used for**: Verifying streaming messages directly on topics.
* **How to run**:
  ```bash
  docker exec -it docker-kafka-1 kafka-console-consumer --topic llm.quality.scores --bootstrap-server kafka:29092 --from-beginning --max-messages 10
  ```

### 6. Redis Queries
* **Used for**: Querying active baseline values and rate-limiting flags in the cache.
* **How to run**:
  ```bash
  docker exec -it quality-engine-redis redis-cli KEYS "baseline:*"
  ```

### 7. Shell / CLI Queries (`type: shell`)
* **Used for**: Host and container-level diagnostics — process inspection, port auditing, network capture, log search, config drift detection, payload parsing, syscall tracing, and systemd journal analysis.
* **Tools covered**: `find`, `grep`, `git`, `ps`, `docker inspect`, `jq`, `ss`, `netstat`, `lsof`, `tcpdump`, `strace`, `journalctl`, `awk`, `sed`.
* **How to run**: All shell queries run directly on the **host shell** unless the query begins with `docker exec`, in which case it targets the named container.
* **Permissions**: `tcpdump`, `strace`, `nsenter`, `lsof`, and kernel log queries require `sudo`.
* **Quick reference by tool**:

| Tool | Purpose in this stack |
|---|---|
| `docker inspect` | Verify container image, env vars, network, healthcheck, and restart policy |
| `ps` | Find runaway threads, zombie processes, and host-level memory hogs |
| `find` | Locate stale lock files, oversized logs, core dumps, and orphaned secrets |
| `grep` | Rank error patterns, catch Kafka failures, scan for OOM events and secret leaks |
| `git` | Detect config drift, correlate deploys with incidents, audit untracked secrets |
| `jq` | Parse and project Kafka payloads, docker-compose service manifests |
| `ss` | Confirm service ports are listening and Kafka consumer connections are live |
| `netstat` | Check for port conflicts on all critical service ports |
| `lsof` | Detect Postgres connection pool exhaustion and FD limit pressure |
| `tcpdump` | Confirm wire-level traffic to Kafka, Postgres, and Redis independently of app logs |
| `strace` | Trace syscalls to find blocked I/O, slow writes, redundant file opens, and missing connections |
| `journalctl` | Read host systemd journal for Docker daemon errors, OOM kills, and kernel network faults |
| `awk` | Compute error rates, latency summaries, score histograms, and consumer lag from raw logs |
| `sed` | Redact secrets, extract span IDs, normalize config values for safe log sharing |
