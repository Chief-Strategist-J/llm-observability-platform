# Observability Infrastructure

Comprehensive observability platform for logs, metrics, and distributed tracing using Temporal workflows.

## 📁 Folder Structure

```
infrastructure/observability/
├── activities/                    # Temporal activities for each pipeline
│   ├── log/                      # Log pipeline activities
│   │   ├── exporters/           # Loki exporter
│   │   │   ├── loki_exporter_activity.py
│   │   │   └── __init__.py
│   │   ├── processors/          # JSON parser
│   │   │   ├── json_parser_activity.py
│   │   │   └── __init__.py
│   │   ├── providers/           # File provider
│   │   │   ├── file_provider_activity.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── *.py                 # 8 log pipeline activities
│   ├── metrics/                  # Metrics pipeline activities
│   │   ├── exporters/           # Prometheus exporter
│   │   │   ├── prometheus_exporter_activity.py
│   │   │   └── __init__.py
│   │   ├── processors/          # Metrics processor
│   │   │   ├── metrics_processor_activity.py
│   │   │   └── __init__.py
│   │   ├── providers/           # Prometheus provider
│   │   │   ├── prometheus_provider_activity.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── *.py                 # 8 metrics pipeline activities
│   ├── tracing/                  # Tracing pipeline activities
│   │   ├── exporters/           # Tempo & Jaeger exporters
│   │   │   ├── tempo_exporter_activity.py
│   │   │   ├── jaeger_exporter_activity.py
│   │   │   └── __init__.py
│   │   ├── processors/          # Span processor
│   │   │   ├── span_processor_activity.py
│   │   │   └── __init__.py
│   │   ├── providers/           # OTLP provider
│   │   │   ├── otlp_provider_activity.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── *.py                 # 9 tracing pipeline activities
│   └── __init__.py
├── config/                       # Configuration
│   ├── constants.py             # Centralized config (NEW)
│   ├── observability_config.py  # Legacy config
│   └── __init__.py
├── workflows/                    # Temporal workflows
│   ├── logs_pipeline_workflow.py
│   ├── metrics_pipeline_workflow.py
│   ├── tracing_pipeline_workflow.py
│   ├── logs_and_metrics_pipeline_workflow.py
│   ├── logs_metrics_tracing_pipeline_workflow.py
│   └── __init__.py
├── workers/                      # Temporal workers
│   ├── logs_pipeline_worker.py
│   ├── metrics_pipeline_worker.py
│   ├── tracing_pipeline_worker.py
│   └── __init__.py
├── triggers/                     # Workflow triggers
│   ├── trigger_logs_pipeline.py
│   ├── trigger_metrics_pipeline.py
│   ├── trigger_tracing_pipeline.py
│   └── __init__.py
├── docs/                         # Documentation
└── README.md                     # This file

```

## 🏗️ Architecture Overview

The observability platform consists of three independent pipelines that can be run separately or together:

### **Logs Pipeline** (Loki + Grafana)
- **Provider**: File-based log collection
- **Processor**: JSON parsing and transformation
- **Exporter**: Push to Loki
- **Datasource**: Auto-configure Grafana

### **Metrics Pipeline** (Prometheus + Grafana)
- **Provider**: Prometheus scrape endpoints
- **Processor**: Metrics transformation and filtering
- **Exporter**: Push to Prometheus
- **Datasource**: Auto-configure Grafana

### **Tracing Pipeline** (Tempo + Grafana)
- **Provider**: OTLP (gRPC/HTTP) endpoints
- **Processor**: Span enrichment
- **Exporter**: Push to Tempo
- **Datasource**: Auto-configure Grafana

Each pipeline follows a consistent pattern:
1. Generate configuration
2. Configure source paths
3. Configure source
4. Deploy processor (OpenTelemetry Collector)
5. Restart source
6. Create Grafana datasource
7. Emit test event
8. Verify event ingestion

## 🚀 Quick Start

### Prerequisites

1. **Temporal Server** (required)
   ```bash
   temporal server start-dev
   ```

2. **Observability Stack** (Docker Compose)
   Ensure the following services are running:
   - Grafana (`grafana-instance-0` on port 3000)
     - Traefik routes: `scaibu.grafana` or `grafana-0.localhost`
   - Loki (`loki-instance-0` on port 3100)
     - Traefik routes: `scaibu.loki` or `loki-0.localhost`
   - Prometheus (`prometheus-instance-0` on port 9090)
     - Traefik routes: `scaibu.prometheus` or `prometheus-0.localhost`
   - Tempo (`tempo-instance-0` on port 3200)
     - Traefik routes: `scaibu.tempo` or `tempo-0.localhost`
   - OpenTelemetry Collector (`otel-collector-instance-0`)
     - Traefik routes: `scaibu.otel` or `otel-0.localhost`
   - Traefik (reverse proxy)

### Running Individual Pipelines

#### Logs Pipeline

**Terminal 1** - Start Worker:
```bash
cd /home/j/live/dinesh/llm-chatbot-python
python infrastructure/observability/workers/logs_pipeline_worker.py
```

**Terminal 2** - Trigger Workflow:
```bash
python infrastructure/observability/triggers/trigger_logs_pipeline.py
```

**Expected Output:**
- Worker processes workflow activities
- Logs ingested to Loki
- Grafana datasource "loki" created
- Test events verified in Loki

---

#### Metrics Pipeline

**Terminal 1** - Start Worker:
```bash
cd /home/j/live/dinesh/llm-chatbot-python
python infrastructure/observability/workers/metrics_pipeline_worker.py
```

**Terminal 2** - Trigger Workflow:
```bash
python infrastructure/observability/triggers/trigger_metrics_pipeline.py
```

**Expected Output:**
- Worker processes workflow activities
- Metrics scraped by Prometheus
- Grafana datasource "prometheus" created
- Test metrics verified in Prometheus

---

#### Tracing Pipeline

**Terminal 1** - Start Worker:
```bash
cd /home/j/live/dinesh/llm-chatbot-python
python infrastructure/observability/workers/tracing_pipeline_worker.py
```

**Terminal 2** - Trigger Workflow:
```bash
python infrastructure/observability/triggers/trigger_tracing_pipeline.py
```

**Expected Output:**
- Worker processes workflow activities
- Traces sent to Tempo
- Grafana datasource "tempo" created
- Test traces verified in Tempo

---

### Running Combined Pipelines

For full observability stack (logs + metrics + tracing):

```bash
# Start combined worker (not yet implemented - use individual workers)
# Or trigger the combined workflow via Temporal UI or CLI

temporal workflow start \
  --task-queue logs-metrics-tracing-queue \
  --type LogsMetricsTracingPipelineWorkflow \
  --workflow-id observability-full-$(date +%s) \
  --input '{}'
```

## 📋 Activities Reference

### Log Activities
- `generate_config_logs` - Generate OpenTelemetry Collector config for logs
- `configure_source_paths_logs` - Configure log file paths
- `configure_source_logs` - Apply log source configuration
- `deploy_processor_logs` - Deploy log processor
- `restart_source_logs` - Restart OpenTelemetry Collector
- `emit_test_event_logs` - Emit synthetic log event
- `verify_event_ingestion_logs` - Verify logs in Loki
- `create_grafana_datasource_activity` - Create Loki datasource in Grafana

### Metrics Activities
- `generate_config_metrics` - Generate OpenTelemetry Collector config for metrics
- `configure_source_paths_metrics` - Configure metrics endpoints
- `configure_source_metrics` - Apply metrics source configuration
- `deploy_processor_metrics` - Deploy metrics processor
- `restart_source_metrics` - Restart OpenTelemetry Collector
- `emit_test_event_metrics` - Emit synthetic metric
- `verify_event_ingestion_metrics` - Verify metrics in Prometheus
- `create_grafana_datasource_metrics` - Create Prometheus datasource in Grafana

### Tracing Activities
- `generate_config_tracings` - Generate OpenTelemetry Collector config for traces
- `configure_source_paths_tracings` - Configure OTLP endpoints
- `configure_source_tracings` - Apply tracing source configuration
- `deploy_processor_tracings` - Deploy trace processor
- `restart_source_tracings` - Restart OpenTelemetry Collector
- `emit_test_event_tracings` - Emit synthetic trace
- `verify_event_ingestion_tracings` - Verify traces in Tempo
- `create_grafana_datasource_tracings_activity` - Create Tempo datasource in Grafana

## 🔌 SDK Integration

Use the observability SDKs from your applications to send telemetry data.

### Python SDK

```python
from observability_sdk import init_observability, get_client

# Initialize observability
init_observability(
    service_name="my-service",
    loki_url="http://localhost:31002",
    prometheus_url="http://localhost:9090",
    tempo_url="http://localhost:4317"
)

# Get client
client = get_client()

# Send logs
client.log("info", "Application started")

# Send metrics
client.counter("requests_total", 1, {"endpoint": "/api/users"})

# Send traces
with client.trace("process_request") as span:
    # Your code here
    span.set_attribute("user_id", "123")
```

### Node.js SDK

```javascript
const { initObservability, getClient } = require('@yourcompany/observability-sdk');

// Initialize
initObservability({
  serviceName: 'my-service',
  lokiUrl: 'http://localhost:31002',
  prometheusUrl: 'http://localhost:9090',
  tempoUrl: 'http://localhost:4317'
});

const client = getClient();

// Send logs
client.log('info', 'Application started');

// Send metrics
client.counter('requests_total', 1, { endpoint: '/api/users' });

// Send traces
await client.withTrace('process_request', async (span) => {
  span.setAttribute('user_id', '123');
  // Your code here
});
```

### Go SDK

```go
import obs "github.com/yourcompany/observability-sdk-go"

// Initialize
obs.InitObservability(obs.Config{
    ServiceName:   "my-service",
    LokiURL:       "http://localhost:31002",
    PrometheusURL: "http://localhost:9090",
    TempoURL:      "http://localhost:4317",
})

client := obs.GetClient()

// Send logs
client.Log("info", "Application started")

// Send metrics
client.Counter("requests_total", 1, map[string]string{"endpoint": "/api/users"})

// Send traces
span := client.StartTrace("process_request")
defer span.End()
span.SetAttribute("user_id", "123")
// Your code here
```

See [sdks/README.md](../../sdks/README.md) for detailed SDK documentation.

## ⚙️ Configuration

### Hostname Configuration

All services use **Traefik-routed hostnames** for proper container-to-container communication:

**Internal Container Names** (for Docker network communication):
```python
loki_url = "http://loki-instance-0:3100"
prometheus_url = "http://prometheus-instance-0:9090" 
tempo_url = "http://tempo-instance-0:3200"
grafana_url = "http://grafana-instance-0:3000"
```

**External Access** (via Traefik):
- Browser/External: `http://scaibu.{service}` (e.g., `http://scaibu.loki`)
- Or: `http://{service}-0.localhost` (e.g., `http://loki-0.localhost`)

**Centralized Configuration** (Recommended):
```python
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG

loki_url = OBSERVABILITY_CONFIG.LOKI_PUSH_URL
prometheus_url = OBSERVABILITY_CONFIG.PROMETHEUS_URL
tempo_url = OBSERVABILITY_CONFIG.TEMPO_URL
grafana_url = OBSERVABILITY_CONFIG.GRAFANA_URL
```

Update `config/constants.py` to change URLs everywhere.

### Worker Configuration

Each worker can be configured via `WorkerConfig`:

```python
cfg = WorkerConfig(
    host="localhost",        # Temporal server host
    port=7233,               # Temporal server port
    queue="<queue-name>",    # Task queue name
    namespace="default",      # Temporal namespace
    max_concurrency=10,      # Max concurrent activities
)
```

### Workflow Parameters

Workflows accept configuration parameters:

```python
params = {
    "dynamic_dir": "infrastructure/orchestrator/dynamicconfig",
    "loki_push_url": "http://loki-instance-0:3100/loki/api/v1/push",
    "loki_query_url": "http://loki-instance-0:3100/loki/api/v1/query",
    "prometheus_url": "http://prometheus-instance-0:9090",
    "tempo_push_url": "http://tempo-instance-0:3200",
    "tempo_query_url": "http://tempo-instance-0:3200",
    "grafana_url": "http://grafana-instance-0:3000",
    "grafana_user": "admin",
    "grafana_password": "SuperSecret123!",
}
```

## 🧪 Testing

### Verify Import Structure

```bash
cd /home/j/live/dinesh/llm-chatbot-python

# Test worker imports
python -c "from infrastructure.observability.workers.logs_pipeline_worker import LogsPipelineWorker"
python -c "from infrastructure.observability.workers.metrics_pipeline_worker import MetricsPipelineWorker"
python -c "from infrastructure.observability.workers.tracing_pipeline_worker import TracingPipelineWorker"

# Test trigger imports
python -c "from infrastructure.observability.triggers.trigger_logs_pipeline import LogsPipelineTrigger"
python -c "from infrastructure.observability.triggers.trigger_metrics_pipeline import MetricsPipelineTrigger"
python -c "from infrastructure.observability.triggers.trigger_tracing_pipeline import TracingPipelineTrigger"
```

### End-to-End Testing

1. **Start Temporal Server**
   ```bash
   temporal server start-dev
   ```

2. **Start All Workers** (in separate terminals)
   ```bash
   python infrastructure/observability/workers/logs_pipeline_worker.py
   python infrastructure/observability/workers/metrics_pipeline_worker.py
   python infrastructure/observability/workers/tracing_pipeline_worker.py
   ```

3. **Trigger Each Workflow** (in separate terminals)
   ```bash
   python infrastructure/observability/triggers/trigger_logs_pipeline.py
   python infrastructure/observability/triggers/trigger_metrics_pipeline.py
   python infrastructure/observability/triggers/trigger_tracing_pipeline.py
   ```

4. **Verify in Grafana**
   - Open http://scaibu.grafana or http://grafana-0.localhost
   - Login: `admin` / `SuperSecret123!`
   - Check datasources: Loki, Prometheus, Tempo
   - Query test data in Explore view

## 🐛 Troubleshooting

### Worker Not Starting

**Problem**: Worker fails to start with import errors

**Solution**:
```bash
# Ensure you're in project root
cd /home/j/live/dinesh/llm-chatbot-python

# Check Python path
export PYTHONPATH=/home/j/live/dinesh/llm-chatbot-python:$PYTHONPATH

# Run worker
python infrastructure/observability/workers/logs_pipeline_worker.py
```

### Temporal Connection Failed

**Problem**: Worker can't connect to Temporal server

**Solution**:
```bash
# Verify Temporal is running
temporal server start-dev

# Check connection
temporal workflow list
```

### Services Not Accessible

**Problem**: Loki/Prometheus/Tempo not reachable

**Solution**:
```bash
# Check Docker services
docker ps | grep -E "loki|prometheus|tempo|grafana"

# Restart services if needed
docker-compose -f infrastructure/orchestrator/config/docker-compose.yml restart
```

### Grafana Datasource Creation Failed

**Problem**: Activity fails to create datasource

**Solution**:
- Verify Grafana is running: `curl http://localhost:31001/api/health`
- Check credentials: default is `admin/SuperSecret123!`
- Check Grafana logs: `docker logs grafana-development`

### Verification Timeouts

**Problem**: `verify_event_ingestion_*` activities timeout

**Solution**:
- Increase timeout in workflow (default 60s)
- Check if test events are being emitted correctly
- Query directly: `curl http://localhost:31002/loki/api/v1/query?query={job="synthetic"}`

## 📊 Monitoring

### View Workflow Execution

```bash
# List all workflows
temporal workflow list

# Describe specific workflow
temporal workflow describe --workflow-id <workflow-id>

# Show workflow history
temporal workflow show --workflow-id <workflow-id>
```

### Access Grafana Dashboards

1. Navigate to http://localhost:31001
2. Login: `admin` / `SuperSecret123!`
3. Go to **Explore**
4. Select datasource (Loki/Prometheus/Tempo)
5. Run queries:
   - **Loki**: `{job="synthetic"}`
   - **Prometheus**: `up`
   - **Tempo**: Search by trace ID

## 🔗 Related Documentation

- [SDKs](../../sdks/README.md) - Multi-language observability SDKs
- [Temporal Documentation](https://docs.temporal.io/) - Temporal workflows guide
- [Grafana Documentation](https://grafana.com/docs/) - Grafana setup and usage
- [OpenTelemetry](https://opentelemetry.io/) - OpenTelemetry Collector

## 🤝 Contributing

When adding new activities:
1. Follow the existing pattern (provider/processor/exporter)
2. Add `__init__.py` to new directories
3. Register activities in the appropriate worker
4. Add tests for the activity
5. Update this README

## 📝 License

[Add your license here]
