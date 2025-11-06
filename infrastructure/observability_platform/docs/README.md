# ONE-COLLECTOR OBSERVABILITY PLATFORM

## Overview

This document outlines the architecture and implementation plan for an organization-wide observability platform using OpenTelemetry Collector and Loki, designed with a modular, activity-based approach and clear priorities (P0, P1, P2, P3). The platform supports logs (P0), with built-in extensibility for metrics (P1) and traces (P2).

## Architecture Overview

```
START: ONE-COLLECTOR OBSERVABILITY PLATFORM
│
? intent = [INGEST | QUERY | ALERT | OPERATE | CONTROL_PLANE | AI_PRODUCT]
│
├─ INGEST  ───────────────────────────────► TREE A  (P0)
├─ QUERY   ───────────────────────────────► TREE B  (P1)
├─ ALERT   ───────────────────────────────► TREE C  (P1)
├─ OPERATE ───────────────────────────────► TREE D  (P0→P1→P2)
├─ CONTROL_PLANE ────────────────────────► TREE E  (P0→P2)
└─ AI_PRODUCT (future ML/analytics) ─────► TREE F  (P3)
```

## System Flow

```
┌─────────────────┐
│ Application Pods │   (no instrumentation needed)
└───────┬─────────┘
        │ stdout logs
        ▼
┌─────────────────────────┐
│ Container Log Files     │  (/var/log/containers/*.log)
└───────┬─────────────────┘
        │ filelog receiver reads files
        ▼
┌──────────────────────────────────┐
│ OpenTelemetry Collector Agent    │ (Single Collector)
│   filelog_receiver()            │
│   + attributes/resource/batch    │
│   + loki_exporter()             │
└───────┬──────────────────────────┘
        │ pushes logs
        ▼
┌────────────────┐
│     Loki       │
└───────┬────────┘
        │ query API
        ▼
┌────────────────┐
│    Grafana     │ (Explore/Alerts)
└────────────────┘
```

## Control Plane Flow

```
       [New Service Starts]
                   │
                   ▼
      ┌────────────────────────┐
      │ DiscoveryService       │ (watches docker/k8s events)
      │ detect_service()       │
      └───────────┬────────────┘
                  │ emits event
                  ▼
      ┌────────────────────────┐
      │ LogSourceRegistry      │
      │ register_log_target()  │
      └───────────┬────────────┘
                  │ fetch registry state
                  ▼
      ┌────────────────────────┐
      │ OtelConfigBuilder      │
      │ generate_config()      │ (log pipeline only in P0)
      └───────────┬────────────┘
                  │ push config
                  ▼
      ┌────────────────────────┐
      │ AgentManager           │
      │ reload_collector()     │ (hot reload, no downtime)
      └───────────┬────────────┘
                  │ verify
                  ▼
      ┌────────────────────────┐
      │ HealthMonitor          │
      │ verify_pipeline_ok()   │
      └───────────┬────────────┘
      if fail:     │
      rollback, alert, retry
```

## TREE A — INGEST (Apps & Containers → OpenTelemetry Collector → Loki)

### Application Code Path (SDK) [P0]
- **OTelCollectorAgent**
  - `filelog_receiver(include_patterns)`
  - `resource_processor()`
  - `attributes_processor(mapping_rules)`
  - `batch_processor(size, timeout)`
  - `loki_exporter(endpoint)`

**Activities:**
- `discover_log_files_activity()`
- `tail_and_ship_logs_activity()`
- `label_enrichment_activity()`

### Container Logs (Agent + Control Plane) [P0→P2]
- **DiscoveryService**
  - `detect_container_log_paths()`
  - `detect_pod_metadata()`
  - `watch_docker_events()`
  - `watch_k8s_api()`
  - `watch_filesystem()`
  - `emit_discovery_event()`

- **LogSourceRegistry**
  - `register_log_target()`
  - `update_source_metadata()`
  - `lookup_sources()`
  - `remove_source()`
  - `list_all_sources()`

- **OtelConfigBuilder**
  - `generate_log_pipeline()`
  - `generate_metrics_pipeline()` (P1)
  - `generate_traces_pipeline()` (P2)

- **AgentManager**
  - `push_config_to_collector()`
  - `reload_collector_service()`
  - `verify_reload_result()`

## TREE B — QUERY (Grafana + API; Logs now, Metrics/Traces later) [P1]

### Human Grafana [P1]
- **LokiQuerierClient**
  - `query_range(query, start, end, limit)`
  - `query_instant(query)`
  - `stream_logs_in_realtime()`
  - `parse_logql_response()`

### Automation API [P2]
- **BatchQueryExecutor**
  - `fan_out_time_windows()`
  - `merge_results()`
  - `backoff_on_rate_limit()`

## TREE C — ALERT (Log-based & metric-based alerts) [P1]

### Loki Ruler [P1]
- **LokiRulerClient**
  - `create_log_alert_rule()`
  - `update_alert_rule()`
  - `delete_alert_rule()`
  - `list_alert_rules()`
  - `test_rule_trigger()`

### Grafana Alerting [P1]
- **AlertGenerator**
  - `generate_alert_thresholds()`
  - `send_alert_notification()`
  - `deduplicate_and_group_alerts()`
  - `silence_alert_temporarily()`

## TREE D — OPERATE (Lifecycle, Scale, Security, SLOs) [P0→P1→P2]

### P0: Loki Lifecycle
- Start/Stop/Restart/Delete Loki
- Verify health

### P1: Distributed Loki + Storage + Frontend
- **ChunkStorageBackend**
  - `upload_chunk(chunk_data, metadata)`
  - `download_chunk(chunk_id)`
  - `list_chunks(prefix)`
  - `verify_storage_health()`
  - `rotate_or_archive_old_chunks()`

- **HealthMonitor**
  - `check_distributor_health()`
  - `check_ingester_health()`
  - `check_querier_health()`
  - `summarize_component_status()`

### P2: Security + Tenancy + SLOs
- **CertManager**
- **GatewayAuthMiddleware**
- **AccessPolicyManager**
- **MetricsCollector**
- **SLOEvaluator**
- **ChaosTester**

## TREE E — CONTROL_PLANE (Discovery → Registry → Config Builder → AgentManager) [P0→P2]

### DiscoveryService
- `watch_docker_events()`
- `watch_k8s_api()`
- `watch_filesystem()`
- `emit_discovery_event()`

### LogSourceRegistry
- `register_source(metadata)`
- `update_source()`
- `delete_source()`
- `list_sources()`

### OtelConfigBuilder
- `load_registry_state()`
- `generate_log_pipeline()`
- `validate_config()`
- `render_yaml()`

### AgentManager
- `push_config_to_collector()`
- `trigger_reload_api()`
- `check_reload_result()`

## TREE F — AI_PRODUCT (Analytics, ML, Monetization) [P3 Future]

### Anomaly Detection & Insights
- Training Data Pipeline
- Model Training & Serving
- Real-time Detection

### Smart Routing & Auto-Remediation
- `recommend_relabel_rules_activity()`
- `auto_rollout_config_activity()`

### Productization & Marketplace
- Package as SaaS
- Self-hosted Helm charts
- Compliance & Telemetry

## Implementation Phases (Detailed Roadmap)

### P0 (Weeks 0–2) — Foundation
- [ ] Loki + Grafana (dev compose)
- [ ] OTel Collector (filelog→Loki)
- [ ] Basic DiscoveryService (docker watcher)
- [ ] LogSourceRegistry (sqlite)
- [ ] OtelConfigBuilder (logs only)
- [ ] AgentManager push & reload
- [ ] Temporal workflow for collector reloads

### P1 (Weeks 3–8) — Production Readiness
- [ ] Distributed Loki + object store
- [ ] Query Frontend + caching
- [ ] LokiRuler alerts + dashboards
- [ ] OTLP receiver + metrics pipeline
- [ ] Auto-instrumentation wrappers
- [ ] Canary reload & rollback

### P2 (Weeks 9–16) — Enterprise Features
- [ ] mTLS & CertManager
- [ ] Per-tenant OrgID
- [ ] Quotas & retention policies
- [ ] SLO monitoring
- [ ] Chaos tests & runbooks

### P3 (Months 4+) — AI/ML & Monetization
- [ ] Training data export pipeline
- [ ] Anomaly detection models
- [ ] Auto-remediation features
- [ ] SaaS packaging & licensing

## Design Principles

1. **Loose Coupling**
   - Event-driven architecture
   - Message bus for inter-service communication
   - Clear API contracts between components

2. **Idempotency**
   - All activities are retryable
   - State transitions are atomic
   - No side effects on retries

3. **Observability**
   - Metrics for all critical paths
   - Structured logging
   - Distributed tracing

4. **Security**
   - mTLS for service communication
   - RBAC for API access
   - Audit logging for all changes

5. **Extensibility**
   - Plugin architecture for collectors/exporters
   - Versioned APIs
   - Backward compatibility guarantees
