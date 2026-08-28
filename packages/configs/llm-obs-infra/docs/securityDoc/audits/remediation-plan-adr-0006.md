# Technical Remediation Plan: Independent Audit of ADR-0006

| Field | Value |
|---|---|
| Target Audit | [independent-audit-adr-0006.md](./independent-audit-adr-0006.md) |
| Target ADR | [infrastructure-resilience-and-edge-case-hardening.md](../../architectureDoc/infrastructure-resilience-and-edge-case-hardening.md) |
| Package | `packages/configs/llm-obs-infra` |
| Scope | 17 Audit Findings (Security, Performance, Resilience, Governance) |
| Status | In Progress |

---

## Executive Summary & Progress Tracking

This document converts the 17 findings from the **Independent Audit of ADR-0006** into an actionable, phased technical implementation plan. Each remediation item specifies the target codebase file, exact root cause, proposed code/config solution, verification command, and progress checkbox.

### Remediation Status Overview

| Phase | Category | Total Items | Completed | Open | Target Completion |
|---|---|---|---|---|---|
| **Phase 1** | Critical Security & Claim Alignment | 4 | 0 | 4 | Sprint 1 |
| **Phase 2** | Operational Hardening & Data-Loss Protection | 6 | 0 | 6 | Sprint 2 |
| **Phase 3** | Production Scale & Load Validation | 7 | 0 | 7 | Sprint 3 |
| **Total** | | **17** | **0** | **17** | |

---

## Phase 1: Critical Security & Claim Alignment (Immediate / High Priority)

### Item 1.1: [Critical] S1 — Remove Unauthenticated Network Signature Claim & Replace Header
- **Finding ID**: `CRIT-S1`
- **Target Files**:
  - `docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md`
  - `scripts/test-health.sh`
- **Problem**: `X-LLMObs-Network-Signature: llmobs-net-sig-v1.0` is a static, unauthenticated header injected by Traefik without dynamic HMAC verification or mTLS authentication. Citing it as an ISO 27001 origin verification control overclaims security posture.
- **Remediation Action**:
  1. Scope documentation to reflect static ingress tracking header (or implement dynamic per-request HMAC verification with secret rotation).
  2. Update ADR-0006 text to remove "Zero-Trust" claims for static header injection.
- **Code / Config Snippet**:
  ```bash
  # Generate HMAC signature in dynamic middleware header if header verification is kept:
  HMAC_SIG=$(echo -n "${TIMESTAMP}:${REQUEST_ID}" | openssl dgst -sha256 -hmac "${SECRET_KEY}" | cut -d' ' -f2)
  ```
- **Verification Command**: `curl -I -k https://localhost:31419`
- **Status**: `[ ]` Incomplete

---

### Item 1.2: [Critical] S2 — Ingest Redaction Position & Plaintext Internal Hop Fix
- **Finding ID**: `CRIT-S2`
- **Target Files**:
  - `docker-compose.yml` (OTel Collector configuration)
  - `config/otel-collector-config.yaml`
- **Problem**: TLS terminates at Traefik, and telemetry spans transit from Traefik to OTel Collector (`:4318`) over HTTP plaintext before the `transform/pii_redaction` processor runs inside the collector. Any compromised container on `llmobs-network` can capture unredacted `sk-...` API keys in transit.
- **Remediation Action**: Move `pii_redaction` processor to the receiver entrypoint, or configure TLS between Traefik and OTel Collector receiver.
- **Code / Config Snippet**:
  ```yaml
  # otel-collector-config.yaml
  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [memory_limiter, transform/pii_redaction, batch]
        exporters: [clickhouse, otlp/tempo]
  ```
- **Verification Command**: Probe network traffic on bridge `llmobs-network` during ingestion to confirm no plaintext API keys appear before redactor.
- **Status**: `[ ]` Incomplete

---

### Item 1.3: [High] S3 — Expand Redaction Coverage to Event Bodies & Expanded Secret Patterns
- **Finding ID**: `HIGH-S3`
- **Target Files**:
  - `config/otel-collector-config.yaml`
- **Problem**: Redaction regex only scans span attributes, missing event payload bodies, resource attributes, and common cloud secrets (AWS `AKIA...`, GCP Service Account JSON, JWTs, PEM private keys).
- **Remediation Action**: Add regex patterns for AWS keys, JWTs, and PEM blocks, and apply `transform` processors across `spans.events` and `resource.attributes`.
- **Code / Config Snippet**:
  ```yaml
  transform/pii_redaction:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - replace_all_patterns(attributes, "value", "AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]")
          - replace_all_patterns(attributes, "value", "eyJ[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]+\\?", "[REDACTED_JWT]")
      - context: event
        statements:
          - replace_all_patterns(attributes, "value", "sk-[a-zA-Z0-9]{32,}", "[REDACTED_API_KEY]")
  ```
- **Verification Command**: `npm run health` with synthetic test span containing `AKIA...` and JWT payloads.
- **Status**: `[ ]` Incomplete

---

### Item 1.4: [High] S4 — Temporal Engine Authentication & mTLS Enforcement
- **Finding ID**: `HIGH-S4`
- **Target Files**:
  - `docker-compose.yml` (`llmobs-temporal` service definition)
- **Problem**: Temporal frontend gRPC (`:7233`) and Web UI (`:8088`) default to unauthenticated access, exposing raw workflow history and unredacted execution state.
- **Remediation Action**: Enable Temporal authentication interceptors or bind Temporal Web UI strictly to localhost / Traefik authenticated proxy.
- **Code / Config Snippet**:
  ```yaml
  # docker-compose.yml
  llmobs-temporal:
    environment:
      - TEMPORAL_AUTH_ENABLED=true
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development.yaml
  ```
- **Verification Command**: `nc -z -w 2 localhost 7233` followed by authenticated gRPC handshake check.
- **Status**: `[ ]` Incomplete

---

## Phase 2: Operational Hardening & Data-Loss Protection

### Item 2.1: [Critical] P1 — Pre-Flight Memory Gate Recalibration
- **Finding ID**: `CRIT-P1`
- **Target Files**:
  - `scripts/prereqs/system-prereqs.sh`
- **Problem**: `verify_system_memory(2500)` checks for 2.5GB free RAM. However, the stack reservations floor is ~5.9GB and max limits sum to ~14.3GB. Hosts clearing 2.5GB panic under real ingestion load.
- **Remediation Action**: Update `system-prereqs.sh` to require at least 6,000MB free RAM (reservation floor) and warn if available memory is below 12,000MB.
- **Code / Config Snippet**:
  ```bash
  # scripts/prereqs/system-prereqs.sh
  verify_system_memory() {
    local min_required_mb=${1:-6000}
    local available_mem_mb=$(free -m | awk '/^Mem:/ {print $7}')
    if [ "$available_mem_mb" -lt "$min_required_mb" ]; then
      echo "ERROR: Insufficient free memory. Required: ${min_required_mb}MB, Available: ${available_mem_mb}MB."
      return 1
    fi
  }
  ```
- **Verification Command**: `./scripts/prereqs/system-prereqs.sh`
- **Status**: `[ ]` Incomplete

---

### Item 2.2: [High] P2 — Automated Disaster Recovery & Volume Backup Pipeline
- **Finding ID**: `HIGH-P2`
- **Target Files**:
  - `scripts/db-backup-and-purge.sh`
  - `docs/architectureDoc/low-level-design.md`
- **Problem**: No automated backup, continuous WAL archiving, or tested restore runbook exists for ClickHouse or AlloyDB Omni data volumes.
- **Remediation Action**: Integrate `pg_dump` snapshot exports and ClickHouse `FREEZE PARTITION` backups into `db-backup-and-purge.sh`.
- **Code / Config Snippet**:
  ```bash
  # scripts/db-backup-and-purge.sh
  docker exec llmobs-alloydb pg_dumpall -U admin > /var/backups/alloydb_$(date +%F).sql
  docker exec llmobs-clickhouse clickhouse-client --query "ALTER TABLE llm_telemetry_analytics.spans_raw FREEZE;"
  ```
- **Verification Command**: `./scripts/db-backup-and-purge.sh --backup`
- **Status**: `[ ]` Incomplete

---

### Item 2.3: [High] P3 — Kafka Replication & Multi-Broker HA Specification
- **Finding ID**: `HIGH-P3`
- **Target Files**:
  - `docker-compose.yml`
  - `docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md`
- **Problem**: Single Kafka broker (`llmobs-kafka`) implies replication factor 1. A crash mid-write results in unflushed log segment data loss.
- **Remediation Action**: Explicitly document single-node topology constraints for dev/staging, and specify 3-broker RF=2 production override compose file.
- **Code / Config Snippet**:
  ```yaml
  # docker-compose.prod.yml
  llmobs-kafka-1:
    environment:
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 2
      KAFKA_DEFAULT_REPLICATION_FACTOR: 2
  ```
- **Verification Command**: `docker exec llmobs-kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic llm.spans.raw`
- **Status**: `[ ]` Incomplete

---

### Item 2.4: [Medium] S5 — Redis ACL Scoping per Consuming Service
- **Finding ID**: `MED-S5`
- **Target Files**:
  - `config/redis.conf`
  - `scripts/orchestrator/stack-orchestration.sh`
- **Problem**: Redis authentication relies on a single shared password granting unrestricted `FLUSHALL` and `CONFIG` access across all services.
- **Remediation Action**: Implement Redis 6+ `ACL SETUSER` commands to grant least-privilege key access to cost workers (`org:*:spend_micro_usd`) and rate limiters (`rate:*:window`).
- **Code / Config Snippet**:
  ```text
  # redis.conf
  user default off
  user cost_worker on >worker_pass ~org:*:spend_micro_usd +@read +@write +hincrby
  user rate_limiter on >limiter_pass ~rate:*:window +@read +@write +zadd +zremrangebyscore
  ```
- **Verification Command**: `docker exec llmobs-redis redis-cli -a worker_pass HINCRBY org:test:spend_micro_usd gpt4 100`
- **Status**: `[ ]` Incomplete

---

### Item 2.5: [Medium] S6 — External Audit Log Storage Isolation
- **Finding ID**: `MED-S6`
- **Target Files**:
  - `docs/securityDoc/security-architecture-review.md`
- **Problem**: `security_audit_logs` lives in the same AlloyDB instance accessible by standard database admin credentials, allowing an attacker to tamper with logs after an incident.
- **Remediation Action**: Mirror audit events to stdout / Docker logging driver shipped to external append-only storage (e.g. S3 Object Lock or CloudWatch).
- **Code / Config Snippet**:
  ```yaml
  logging:
    driver: "json-file"
    options:
      max-size: "100m"
      max-file: "10"
  ```
- **Verification Command**: Verify Docker container log driver output via `docker logs llmobs-alloydb`.
- **Status**: `[ ]` Incomplete

---

### Item 2.6: [Medium] S8 — Safe Process Ownership Validation in `port-manager.sh`
- **Finding ID**: `MED-S8`
- **Target Files**:
  - `scripts/orchestrator/port-manager.sh`
- **Problem**: `free_all_ports()` executes `fuser -k` / `kill -9` on any process bound to ports `31410–31425` without checking Docker container or cgroup ownership, risking termination of unrelated host processes.
- **Remediation Action**: Inspect process command line / cgroup before issuing `kill -9`. If process belongs to another application, fail safely with an error message.
- **Code / Config Snippet**:
  ```bash
  # scripts/orchestrator/port-manager.sh
  safe_kill_port() {
    local port=$1
    local pid=$(lsof -t -i:${port})
    if [ -n "$pid" ]; then
      if grep -q "docker" /proc/${pid}/cgroup 2>/dev/null; then
        echo "Killing stale Docker process $pid on port $port"
        kill -9 $pid
      else
        echo "WARNING: Port $port is occupied by host process $pid. Skipping kill."
      fi
    fi
  }
  ```
- **Verification Command**: `./scripts/orchestrator/port-manager.sh`
- **Status**: `[ ]` Incomplete

---

## Phase 3: Production Capacity & Scale Hardening

### Item 3.1: [Medium] P4 — Cgroup OOM-Kill Recovery & Crash-Loop Detection
- **Finding ID**: `MED-P4`
- **Target Files**:
  - `docker-compose.yml`
  - `scripts/test-health.sh`
- **Problem**: Memory cgroup limits trigger container SIGKILL during spikes, but no crash-loop detection or automated recovery alert exists.
- **Remediation Action**: Add `restart: on-failure:5` policy and monitor restart counts in `test-health.sh`.
- **Code / Config Snippet**:
  ```yaml
  deploy:
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 5
      window: 120s
  ```
- **Verification Command**: `./scripts/test-health.sh`
- **Status**: `[ ]` Incomplete

---

### Item 3.2: [Medium] P5 — Horizontal Scaling Strategy for OTel Collector
- **Finding ID**: `MED-P5`
- **Target Files**:
  - `docs/architectureDoc/high-level-design.md`
  - `docker-compose.yml`
- **Problem**: A single OTel Collector container creates a bottleneck for high-throughput span ingestion.
- **Remediation Action**: Document Traefik load-balanced collector replicas and expose configuration template.
- **Code / Config Snippet**:
  ```yaml
  llmobs-otel-collector:
    deploy:
      replicas: 3
  ```
- **Verification Command**: `docker compose ps llmobs-otel-collector`
- **Status**: `[ ]` Incomplete

---

### Item 3.3: [Medium] P6 — Synthetic Load Test & Latency Baseline Validation
- **Finding ID**: `MED-P6`
- **Target Files**:
  - `docs/performanceDoc/load-stress-test-report.md`
  - `scripts/test-health.sh`
- **Problem**: "Production-grade" throughput claims lack empirical k6 / load test execution output.
- **Remediation Action**: Add automated 1,000 req/sec burst test stage to health verification script.
- **Code / Config Snippet**:
  ```bash
  # Run k6 load test script
  k6 run --vus 50 --duration 30s scripts/loadtest/span-ingestion-k6.js
  ```
- **Verification Command**: `./scripts/test-health.sh --load-test`
- **Status**: `[ ]` Incomplete

---

### Item 3.4: [Low] P7 — Hard Timeouts on Retry Polling Loops
- **Finding ID**: `LOW-P7`
- **Target Files**:
  - `scripts/orchestrator/stack-orchestration.sh`
- **Problem**: Polling loops for DB readiness lack max iteration ceilings, risking infinite hangs if disk fills or migrations fail.
- **Remediation Action**: Add max counter (e.g. 30 attempts x 5s = 150s max timeout) to `wait_for_*` functions.
- **Code / Config Snippet**:
  ```bash
  wait_for_alloydb() {
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
      if pg_isready -h localhost -p 31420; then return 0; fi
      attempt=$((attempt + 1))
      sleep 5
    done
    echo "ERROR: AlloyDB readiness timeout exceeded."
    return 1
  }
  ```
- **Verification Command**: `./scripts/orchestrator/stack-orchestration.sh`
- **Status**: `[ ]` Incomplete

---

### Item 3.5: [Low] P8 — ClickHouse Concurrent Query Ceiling Configuration
- **Finding ID**: `LOW-P8`
- **Target Files**:
  - `config/clickhouse-config.xml`
- **Problem**: `max_memory_usage` is bounded per query, but no `max_concurrent_queries` or `max_memory_usage_for_all_queries` limit exists, risking aggregate OOM panics during concurrent Grafana dashboard refreshes.
- **Remediation Action**: Set `max_concurrent_queries` to 100 and `max_memory_usage_for_all_queries` to 3,221,225,472 (3GB).
- **Code / Config Snippet**:
  ```xml
  <clickhouse>
      <profiles>
          <default>
              <max_concurrent_queries>100</max_concurrent_queries>
              <max_memory_usage_for_all_queries>3221225472</max_memory_usage_for_all_queries>
          </default>
      </profiles>
  </clickhouse>
  ```
- **Verification Command**: `docker exec llmobs-clickhouse clickhouse-client --query "SELECT value FROM system.settings WHERE name = 'max_concurrent_queries'"`
- **Status**: `[ ]` Incomplete

---

### Item 3.6: [Low] S9 — Pinning CA Certificates in HTTPS Verification Probes
- **Finding ID**: `LOW-S9`
- **Target Files**:
  - `scripts/test-health.sh`
- **Problem**: `check_http` uses `curl -sk` (`--insecure`), disabling TLS certificate verification during health checks.
- **Remediation Action**: Replace `-k` with `--cacert config/certs/ca.pem` to validate TLS certificate chains properly.
- **Code / Config Snippet**:
  ```bash
  check_http_secure() {
    curl -s --cacert config/certs/ca.pem https://localhost:31419/healthz
  }
  ```
- **Verification Command**: `./scripts/test-health.sh`
- **Status**: `[ ]` Incomplete

---

### Item 3.7: [Medium] S7 — Service-to-Service SASL & Write Authentication
- **Finding ID**: `MED-S7`
- **Target Files**:
  - `docker-compose.yml`
  - `config/otel-collector-config.yaml`
- **Problem**: Internal container calls to Kafka and ClickHouse write endpoints lack SASL or bearer authentication.
- **Remediation Action**: Enable Kafka `SASL_PLAINTEXT` for internal topics and require ClickHouse HTTP Basic Auth for OTel Collector exports.
- **Code / Config Snippet**:
  ```yaml
  exporters:
    clickhouse:
      endpoint: "tcp://llmobs-clickhouse:9000?username=otel_user&password=otel_password"
  ```
- **Verification Command**: `docker exec llmobs-otel-collector ./otelcol-contrib validate`
- **Status**: `[ ]` Incomplete

---

## Verification & Execution Protocol

1. **Local Test Execution**: Before committing any remediation task, execute `./scripts/test-health.sh` to confirm stack health.
2. **Updating Status**: Upon successful implementation and verification of an item, update the checkbox in this document from `[ ]` to `[x]`.
3. **Commit Naming**: Commit remediation patches using clean conventional commit format:
   `fix(infra): resolve audit finding CRIT-P1 - update system memory pre-flight gate`
