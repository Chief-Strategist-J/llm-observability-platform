# OpenTelemetry Observability Setup

This directory contains a comprehensive OpenTelemetry collector setup for collecting **logs**, **metrics**, and **traces** from your LLM chatbot application.

## 🏗️ Architecture Overview

The observability stack consists of:

### 1. **OpenTelemetry Collector** (otel/opentelemetry-collector-contrib)
- **Purpose**: Central telemetry data collection and forwarding
- **Receivers**: OTLP, filelog, hostmetrics, docker_stats
- **Processors**: batch, resource_detection, attributes
- **Exporters**: logging, OTLP (Jaeger), Prometheus, Loki

### 2. **Jaeger** (jaegertracing/all-in-one)
- **Purpose**: Distributed tracing and performance monitoring
- **UI**: http://localhost:16686
- **Receives traces from**: OpenTelemetry Collector

### 3. **Prometheus** (prom/prometheus)
- **Purpose**: Metrics collection and alerting
- **UI**: http://localhost:9090
- **Receives metrics from**: OpenTelemetry Collector, applications

### 4. **Loki** (grafana/loki)
- **Purpose**: Log aggregation and querying
- **UI**: http://localhost:3100 (via Grafana)
- **Receives logs from**: OpenTelemetry Collector

## 📁 Configuration Files

### `telemetry.yaml` - Main Pipeline Configuration
Defines the telemetry pipelines for traces, metrics, and logs.

### `receivers.yaml` - Data Receivers
- **OTLP**: Standard OpenTelemetry protocol (gRPC:4317, HTTP:4318)
- **filelog**: File-based log collection with regex parsing
- **hostmetrics**: System metrics (CPU, memory, disk, network)
- **docker_stats**: Docker container metrics

### `processors.yaml` - Data Processing
- **batch**: Batching for performance optimization
- **resource_detection**: Automatic resource attribute detection
- **attributes**: Custom attribute enrichment
- **memory_limiter**: Memory usage control

### `exporters.yaml` - Data Exporters
- **logging**: Debug logging exporter
- **otlp**: Forward traces to Jaeger
- **prometheus**: Export metrics to Prometheus
- **loki**: Forward logs to Loki

## 🚀 Activities

### Individual Service Activities

#### `opentelemetry_collector_activity.py`
```python
# Start OpenTelemetry Collector
await start_opentelemetry_collector("my-service")

# Get status
status = await get_opentelemetry_collector_status("my-service")

# Stop collector
await stop_opentelemetry_collector("my-service")
```

#### `jaeger_activity.py`
```python
# Start Jaeger for tracing
await start_jaeger_container("my-service")

# Get status
status = await get_jaeger_status("my-service")
```

#### `prometheus_activity.py`
```python
# Start Prometheus for metrics
await start_prometheus_container("my-service")

# Get status
status = await get_prometheus_status("my-service")
```

#### `loki_activity.py`
```python
# Start Loki for logs
await start_loki_container("my-service")

# Get status
status = await get_loki_status("my-service")
```

### Configuration Activities

#### `configure_opentelemetry_activity.py`
```python
# Configure OpenTelemetry Collector
success = await configure_opentelemetry_collector("my-service")

# Validate configuration
validation = await validate_opentelemetry_config("my-service")

# Update configuration
await update_opentelemetry_config("my-service", {"telemetry": {"log_level": "DEBUG"}})
```

### Orchestration Activities

#### `observability_stack_activity.py`
```python
# Setup complete observability stack
results = await setup_complete_observability_stack("my-service")
# Returns: {"success": true, "services": {...}, "summary": {...}}

# Get stack status
status = await get_observability_stack_status("my-service")

# Stop entire stack
success = await stop_observability_stack("my-service")

# Restart entire stack
results = await restart_observability_stack("my-service")
```

## 📊 Telemetry Data Flow

### Traces Flow
1. **Application** → OTLP → **OpenTelemetry Collector** → **Jaeger**
2. View traces at: http://localhost:16686

### Metrics Flow
1. **Application/System** → OTLP → **OpenTelemetry Collector** → **Prometheus**
2. View metrics at: http://localhost:9090

### Logs Flow
1. **Application Files** → filelog → **OpenTelemetry Collector** → **Loki**
2. View logs via Grafana: http://localhost:3000

## 🔧 Setup Instructions

### 1. Prerequisites
- Docker and Docker Compose
- Python 3.12+ with required packages
- Network connectivity

### 2. Quick Setup (Recommended)
```python
from infrastructure.orchestrator.activities.common_activity.observability_stack_activity import (
    setup_complete_observability_stack
)

# Setup entire observability stack
results = await setup_complete_observability_stack("llm-chatbot")
print(f"Setup successful: {results['success']}")
print(f"Access URLs: {results['summary']['access_urls']}")
```

### 3. Manual Setup
```python
# Configure OpenTelemetry Collector
await configure_opentelemetry_collector("llm-chatbot")

# Start individual services
await start_loki_container("llm-chatbot")        # Logs
await start_prometheus_container("llm-chatbot")  # Metrics
await start_jaeger_container("llm-chatbot")      # Traces
await start_opentelemetry_collector("llm-chatbot")  # Collector
```

## 📈 Usage Examples

### Sending Telemetry Data

#### Python Application Example
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True,
)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create spans
with tracer.start_as_current_span("llm_request") as span:
    span.set_attribute("user_id", "user123")
    span.set_attribute("model", "gpt-3.5-turbo")
    # Your LLM logic here
```

#### Log Configuration Example
Configure your application to write structured logs:
```json
{
  "timestamp": "2025-01-17 14:32:05",
  "level": "INFO",
  "message": "Processing LLM request",
  "user_id": "user123",
  "model": "gpt-3.5-turbo",
  "request_id": "req_abc123"
}
```

### Configuration Customization

#### Custom Receivers
Edit `receivers.yaml`:
```yaml
filelog:
  include: [/var/log/myapp/*.log, /var/log/custom/*.log]
  operators:
    - type: json_parser  # For JSON logs
    - type: regex_parser  # For structured text logs
```

#### Custom Processors
Edit `processors.yaml`:
```yaml
attributes:
  actions:
    - key: environment
      action: upsert
      value: "production"
    - key: service.version
      action: upsert
      value: "2.1.0"
```

## 🔍 Monitoring and Troubleshooting

### Health Checks
```python
# Check individual service status
jaeger_status = await get_jaeger_status("my-service")
prometheus_status = await get_prometheus_status("my-service")
loki_status = await get_loki_status("my-service")
otel_status = await get_opentelemetry_collector_status("my-service")

# Check complete stack status
stack_status = await get_observability_stack_status("my-service")
```

### Common Issues

#### Port Conflicts
- **Problem**: Port already in use
- **Solution**: Check `docker ps` and stop conflicting containers
- **Alternative**: Modify port mappings in activity configurations

#### Configuration Errors
- **Problem**: OpenTelemetry Collector fails to start
- **Solution**: Validate configuration with `validate_opentelemetry_config()`
- **Check**: Review logs in Docker container

#### Network Issues
- **Problem**: Services can't communicate
- **Solution**: Ensure all services are on the same Docker network
- **Default Network**: `observability-network`

### Log Locations
- **OpenTelemetry Collector**: `docker logs opentelemetry-collector-development`
- **Jaeger**: `docker logs jaeger-development`
- **Prometheus**: `docker logs prometheus-development`
- **Loki**: `docker logs loki-development`

## 🎯 Best Practices

### 1. Resource Optimization
- Monitor memory usage: Each service has resource limits configured
- Scale based on load: Adjust CPU/memory limits in CONFIG dictionaries

### 2. Security Considerations
- **Development**: Insecure connections enabled for simplicity
- **Production**: Enable TLS and authentication
- **Network**: Use internal Docker networks for isolation

### 3. Performance Tuning
- **Batch Size**: Adjust batch processor settings based on throughput
- **Sampling**: Configure appropriate sampling rates for high-volume applications
- **Retention**: Configure data retention policies in each service

### 4. High Availability
- **Volumes**: All services use persistent volumes for data
- **Restart Policies**: Configured to restart automatically
- **Health Checks**: Built-in readiness and liveness probes

## 📚 Integration with Grafana

Configure Grafana datasources to visualize all telemetry data:

### Datasource Configuration (`datasources.yaml`)
```yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
  - name: Jaeger
    type: jaeger
    url: http://jaeger:16686
  - name: Loki
    type: loki
    url: http://loki:3100
```

## 🚨 Alerting Setup

Configure Prometheus alerts in `prometheus.yml`:
```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 📞 Support

For issues or questions:
1. Check service logs: `docker logs <container-name>`
2. Validate configuration: Use `validate_opentelemetry_config()`
3. Check network connectivity: `docker network ls`
4. Review resource usage: `docker stats`

## 🔄 Updates and Maintenance

To update the observability stack:
1. **Backup data**: Ensure volumes are backed up
2. **Update images**: Pull latest images in activity configurations
3. **Test configuration**: Validate after updates
4. **Restart services**: Use `restart_observability_stack()`
