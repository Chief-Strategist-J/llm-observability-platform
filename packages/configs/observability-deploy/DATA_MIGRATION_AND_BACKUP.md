# Data Backup & Migration Strategy

This guide outlines the data backup procedures and step-by-step zero-downtime migration strategy for PostgreSQL, ClickHouse, and Redis datastores in the LLM Observability Platform.

---

## 1. Data Backup Strategy

Stateful data backups are automated daily and stored in encrypted Cloud Storage buckets (AWS S3 or GCP Cloud Storage).

### A. PostgreSQL Backup (Metadata & Alerts)
- **Method**: Hot backup using `pg_dump` to prevent database locking.
- **Local Command**:
  ```bash
  pg_dump -h localhost -U postgres -d llm_observability -F c -b -v -f /backups/postgres_$(date +%F).dump
  ```
- **Restore Command**:
  ```bash
  pg_restore -h localhost -U postgres -d llm_observability -v /backups/postgres_xxxx-xx-xx.dump
  ```

### B. ClickHouse Backup (Columnar Telemetry Logs)
- **Method**: Uses ClickHouse's native partition `FREEZE` command to create metadata snapshots, or the `clickhouse-backup` open-source utility.
- **Local Freeze Command**:
  ```bash
  clickhouse-client --query "ALTER TABLE llm_spans FREEZE WITH NAME 'backup_$(date +%F)'"
  ```
- **Restore Command**:
  Copy the frozen partition files back into the ClickHouse `shadow/` directory and run:
  ```bash
  ALTER TABLE llm_spans ATTACH MERGE TREE PARTITION 'partition_name' FROM 'backup_name'
  ```

### C. Redis Backup (Cache & Baseline Sketches)
- **Method**: Triggers asynchronous background snapshotting (`BGSAVE`) and archives the resulting `dump.rdb` file.
- **Local Command**:
  ```bash
  redis-cli BGSAVE
  # Wait for save completion
  cp /var/lib/redis/data/dump.rdb /backups/redis_$(date +%F).rdb
  ```

---

## 2. Zero-Downtime Data Migration Strategy

To transition from legacy or local databases to the cloud-native observability stack without interrupting telemetry ingestion, the following 5-phase migration lifecycle must be strictly enforced:

```
[Phase 1: Shadow Writes] ──> [Phase 2: Parity Verification] ──> [Phase 3: Flip Reads]
                                  (14 days minimum)
                                          │
                                          ▼
[Phase 5: Cold Archiving] <── [Phase 4: Deprecate Legacy]
                                  (30 days minimum)
```

### Phase 1: Shadow Writes (Dual Ingestion)
- **Action**: Modify the telemetry client/api configuration to route writes to **both** the legacy datastore and the new Cloud/observability stack.
- **Ingress**: All ingestion APIs write synchronously to legacy storage, and asynchronously (with failure protection) to the new Kafka/PostgreSQL.
- **User Impact**: Zero. Readers continue consuming from the legacy datastore.

### Phase 2: Parity Verification
- **Action**: Run automated verification scripts to compare the data consistency between the legacy datastore and the new stack.
- **Verification Criteria**:
  - Compare total row counts of ingested spans in clickhouse.
  - Verify DDSketch bucket hashes and percentile distributions.
  - Assert relational schema constraint integrity in Postgres.
- **Duration**: **Minimum 14 days** of continuous shadow writing with 100% parity must pass before progressing.

### Phase 3: Flip Reads (Primary Switch)
- **Action**: Configure API queries to retrieve dashboard analytics and metrics from the **new stack** as primary.
- **Fallback**: Enable automated fallback to the legacy database on connection failure or query timeout.
- **Monitoring**: Alert on any fallback triggers; these indicate gaps or connection anomalies in the new stack.

### Phase 4: Deprecate Legacy Writes
- **Action**: Cut off the shadow write path to the legacy databases. Disable writes completely, making the legacy databases read-only.
- **Duration**: Maintain the legacy stack in read-only state for **minimum 30 days** to ensure the new cluster handles query load and edge scenarios stably.

### Phase 5: Decommission and Cold Archiving
- **Action**: Export final database dumps of the legacy systems to cold storage (e.g. Glacier or Archive Tier), verify the completeness of the exports, and terminate the old legacy VM instances or database nodes.
