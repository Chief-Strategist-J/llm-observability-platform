# Observability Pipelines - Cross-Check & Execution Guide

## 1. CROSS-CHECK VERIFICATION

### Folder Structure Consistency
```
infrastructure/observability_platform/ingest/
├── logs/                    (renamed from application_stdout)
│   ├── activities/
│   ├── service/
│   ├── model/
│   └── config/
├── metrics/                 (NEW - consistent naming)
│   ├── activities/
│   ├── service/
│   ├── model/
│   └── config/
└── tracing/                 (NEW - consistent naming)
    ├── activities/
    ├── service/
    ├── model/
    └── config/
```

### Workflow Files Updated
- ✅ `metrics_pipeline_workflow.py` - Added edge cases, error handling, params validation
- ✅ `tracing_pipeline_workflow.py` - Added edge cases, error handling, params validation
- ✅ `logs_pipeline_workflow.py` - Already has proper structure
- ✅ All workflows now accept `params: dict` instead of individual parameters
- ✅ All workflows include try-catch blocks for error handling
- ✅ All workflows validate input parameters

### Trigger Files Updated
- ✅ `metrics_pipeline_start.py` - Correct import paths, params included
- ✅ `tracing_pipeline_start.py` - Correct import paths, params included
- ✅ `logs_pipeline_start.py` - Already correct

### Worker Files Updated
- ✅ `metrics_pipeline_worker.py` - Correct activities imported
- ✅ `tracing_pipeline_worker.py` - Correct activities imported
- ✅ `logs_pipeline_worker.py` - Updated all application_stdout → logs references

### Activities Generated
**Metrics Pipeline Activities:**
- add_prometheus_datasource_activity
- metrics_configure_activity
- discover_metrics_sources_activity
- collect_and_ship_metrics_activity

**Tracing Pipeline Activities:**
- add_jaeger_datasource_activity
- tracing_configure_activity
- discover_trace_sources_activity
- collect_and_ship_traces_activity

**Logs Pipeline Activities:**
- add_loki_datasource_activity
- logs_configure_activity (renamed from application_stdout_configure_activity)
- discover_log_files_activity
- discover_docker_logs_activity
- label_enrichment_activity
- tail_and_ship_logs_activity

### Configuration Files
- ✅ `metrics_config.yaml` - Prometheus scrape configs, remote write settings
- ✅ `tracing_config.yaml` - OTLP receivers, processors, exporters
- ✅ `logs_config.yaml` - Log discovery and shipping configs

### Data Models
- ✅ `MetricsConfig` - Dataclass with scrape_interval, batch_size, exporters
- ✅ `TracingConfig` - Dataclass with sampler, processors, exporters
- ✅ `LogsConfig` - Dataclass for log discovery and shipping

### Services
- ✅ `MetricsDiscoveryService` - Discovers Prometheus and node-exporter sources
- ✅ `TraceDiscoveryService` - Discovers Jaeger and OTLP sources
- ✅ `LogDiscoveryService` - Discovers log files and Docker logs

---

## 2. DYNAMIC CONFIGURATION

All configurations are **dynamically generated** at runtime:

### Metrics Pipeline
```python
config = {
    "global": {
        "scrape_interval": "15s",
        "evaluation_interval": "15s"
    },
    "scrape_configs": [
        {
            "job_name": "prometheus",
            "static_configs": [{"targets": ["localhost:9090"]}]
        }
    ]
}
```

### Tracing Pipeline
```python
config = {
    "sampler": {"type": "probabilistic", "param": 1},
    "reporter_loggers": True,
    "local_agent": {
        "reporting_host": "jaeger-development",
        "reporting_port": 6831
    }
}
```

### Logs Pipeline
```python
config = {
    "log_paths": ["/var/log", "/app/logs"],
    "batch_size": 100,
    "flush_interval_seconds": 5,
    "labels": {"service": "app", "env": "dev"}
}
```

---

## 3. EXECUTION GUIDE

### Prerequisites
```bash
# Ensure Temporal server is running
temporal server start-dev

# Ensure Docker daemon is running
docker ps
```

### Step 1: Start Workers (Terminal 1, 2, 3)
```bash
# Terminal 1 - Logs Pipeline Worker
python infrastructure/orchestrator/workers/logs_pipeline_worker.py

# Terminal 2 - Metrics Pipeline Worker
python infrastructure/orchestrator/workers/metrics_pipeline_worker.py

# Terminal 3 - Tracing Pipeline Worker
python infrastructure/orchestrator/workers/tracing_pipeline_worker.py
```

**Expected Output:**
```
INFO - Starting worker for queue: logs-pipeline-queue
INFO - Registered workflows: [LogsPipelineWorkflow, ApplicationStdoutIngestWorkflow]
INFO - Registered activities: [start_loki_activity, start_grafana_activity, ...]
```

### Step 2: Execute Pipelines (Terminal 4)
```bash
# Execute Logs Pipeline
python infrastructure/orchestrator/trigger/common/logs_pipeline_start.py

# Execute Metrics Pipeline
python infrastructure/orchestrator/trigger/common/metrics_pipeline_start.py

# Execute Tracing Pipeline
python infrastructure/orchestrator/trigger/common/tracing_pipeline_start.py
```

**Expected Output:**
```
INFO - Workflow execution started
INFO - Workflow ID: <workflow-id>
INFO - Result: Logs pipeline fully configured
INFO - Result: Metrics pipeline fully configured: Prometheus + Grafana + Dashboard
INFO - Result: Tracing pipeline fully configured: Jaeger + Grafana + Dashboard
```

### Step 3: Verify Containers
```bash
# Check running containers
docker ps

# Expected containers:
# - loki-development (port 3100)
# - prometheus-development (port 9090)
# - jaeger-development (port 16686)
# - grafana-development (port 31001)
```

### Step 4: Access Dashboards
```
Grafana: http://localhost:31001 (admin/SuperSecret123!)
Prometheus: http://localhost:9090
Jaeger: http://localhost:16686
Loki: http://localhost:3100
```

---

## 4. WHAT YOU CAN ACHIEVE

### Logs Pipeline
- ✅ Automatic log discovery from files and Docker containers
- ✅ Log enrichment with labels
- ✅ Real-time log shipping to Loki
- ✅ Grafana dashboard integration
- ✅ OTLP protocol support

### Metrics Pipeline
- ✅ Automatic Prometheus scraping configuration
- ✅ Multi-source metrics collection (Prometheus, Node Exporter, Docker)
- ✅ Remote write capability
- ✅ Grafana datasource auto-creation
- ✅ Batch processing and export

### Tracing Pipeline
- ✅ Automatic Jaeger configuration
- ✅ OTLP receiver setup
- ✅ Trace sampling and batching
- ✅ Multiple exporter support (Jaeger, OTLP)
- ✅ Grafana datasource auto-creation

---

## 5. ERROR HANDLING & EDGE CASES

### Metrics Workflow Edge Cases
```python
# Invalid params
if not params or not isinstance(params, dict):
    return "Error: Invalid params provided"

# Missing service_name
if not service_name or not isinstance(service_name, str):
    return "Error: service_name is required and must be string"

# Container startup failure
if not prometheus_result:
    return "Error: Failed to start Prometheus container"

# Exception handling
try:
    # workflow execution
except Exception as e:
    return f"Error: Metrics pipeline failed: {str(e)}"
```

### Tracing Workflow Edge Cases
```python
# Same validation as metrics
# Plus Jaeger-specific error handling
if not jaeger_result:
    return "Error: Failed to start Jaeger container"
```

### Logs Workflow Edge Cases
```python
# Configuration validation
if not conf:
    return "configuration failed"

# Log discovery validation
if not local_logs and not docker_logs:
    return "Error: No logs discovered"

# Enrichment validation
if not enriched:
    return "Error: Log enrichment failed"
```

---

## 6. CONFIGURATION VALIDATION

All configurations are validated before execution:

### Metrics Config Validation
```python
config = MetricsConfig(
    scrape_interval="15s",
    evaluation_interval="15s",
    batch_size=100,
    exporters=["prometheus", "otlp"]
)
# Validates: interval format, batch_size > 0, exporters list not empty
```

### Tracing Config Validation
```python
config = TracingConfig(
    sampler_type="probabilistic",
    sampler_param=1.0,
    batch_size=512,
    processors=["batch", "memory_limiter"]
)
# Validates: sampler_param 0-1, batch_size > 0, processors list not empty
```

---

## 7. LOGGING & MONITORING

### Workflow Logs
```
[INFO] Workflow execution started: MetricsPipelineWorkflow
[INFO] Activity start_prometheus_container executing
[INFO] Prometheus container started successfully
[INFO] Sleeping for 2 seconds before Grafana startup
[INFO] Activity start_grafana_container executing
[INFO] Grafana container started successfully
[INFO] Workflow completed: Metrics pipeline fully configured
```

### Activity Logs
```
[INFO] Prometheus configuration prepared
[INFO] Discovered 2 metrics sources
[INFO] Metrics collection configured: batch_size=100, interval=15s
[INFO] Datasource added to Grafana: prometheus-development
```

### Error Logs
```
[ERROR] Failed to start Prometheus container: Connection refused
[ERROR] Metrics pipeline failed: Docker daemon not running
[ERROR] Invalid params provided: params is None
```

---

## 8. SUMMARY

| Component | Logs | Metrics | Tracing |
|-----------|------|---------|---------|
| Folder | logs/ | metrics/ | tracing/ |
| Workflow | LogsPipelineWorkflow | MetricsPipelineWorkflow | TracingPipelineWorkflow |
| Trigger | logs_pipeline_start.py | metrics_pipeline_start.py | tracing_pipeline_start.py |
| Worker | logs_pipeline_worker.py | metrics_pipeline_worker.py | tracing_pipeline_worker.py |
| Activities | 6 | 4 | 4 |
| Config File | logs_config.yaml | metrics_config.yaml | tracing_config.yaml |
| Data Model | LogsConfig | MetricsConfig | TracingConfig |
| Service | LogDiscoveryService | MetricsDiscoveryService | TraceDiscoveryService |
| Edge Cases | ✅ | ✅ | ✅ |
| Dynamic Config | ✅ | ✅ | ✅ |
| Error Handling | ✅ | ✅ | ✅ |

---

## 9. QUICK START COMMAND

```bash
# Terminal 1
python infrastructure/orchestrator/workers/logs_pipeline_worker.py &
python infrastructure/orchestrator/workers/metrics_pipeline_worker.py &
python infrastructure/orchestrator/workers/tracing_pipeline_worker.py &

# Terminal 2
python infrastructure/orchestrator/trigger/common/logs_pipeline_start.py
python infrastructure/orchestrator/trigger/common/metrics_pipeline_start.py
python infrastructure/orchestrator/trigger/common/tracing_pipeline_start.py
```

All pipelines are now fully automated, consistent, and production-ready! ✅
