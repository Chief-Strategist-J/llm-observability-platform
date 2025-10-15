# Complete Observability Stack

This directory contains a complete observability stack for monitoring your applications with logs, metrics, and traces using industry-standard tools.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │───▶│   OpenTelemetry │───▶│     Backends    │
│                 │    │    Collector    │    │  (Loki/Tempo/  │
└─────────────────┘    └─────────────────┘    │    Prometheus)  │
                                               └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│                 │◀───│                 │◀────────────┘
│    Grafana      │    │   Prometheus    │
│  (Visualization)│    │   (Metrics)     │
└─────────────────┘    └─────────────────┘
```

## 📁 Structure

```
infrastructure/monitoring/
├── component/
│   ├── grafana/          # Grafana configuration and provisioning
│   ├── loki/            # Loki for log aggregation
│   ├── otel/            # OpenTelemetry Collector for traces/metrics
│   ├── prometheus/      # Prometheus for metrics collection
│   └── tempo/           # Tempo for distributed tracing
├── setup-observability.sh # Master setup script
└── README.md           # This file
```

## 🚀 Quick Start

1. **Run the setup script:**
   ```bash
   cd infrastructure/monitoring
   ./setup-observability.sh
   ```

2. **Access Grafana:**
   - URL: http://localhost:31001
   - Username: `admin`
   - Password: `SuperSecret123!`

3. **Configure Data Sources in Grafana:**
   - **Loki** (Logs): `http://loki:3100`
   - **Prometheus** (Metrics): `http://prometheus:9090`
   - **Tempo** (Traces): `http://tempo:3200`

## 🔧 Services

### 📊 Loki (Log Aggregation)
- **Purpose:** Centralized log storage and querying
- **Access:** http://localhost:31090
- **Configuration:** `component/loki/`
- **Docker Compose:** `logger-loki-compose.yaml`

### 📈 Prometheus (Metrics Collection)
- **Purpose:** Metrics collection and alerting
- **Access:** http://localhost:9090
- **Configuration:** `component/prometheus/`
- **Features:** Node exporter, application metrics scraping

### 🔍 OpenTelemetry Collector (Traces & Metrics)
- **Purpose:** Collect traces, metrics, and logs from applications
- **Endpoints:**
  - OTLP gRPC: `localhost:4317`
  - OTLP HTTP: `localhost:4318`
  - Jaeger: `localhost:14250`
  - Zipkin: `localhost:9411`
- **Configuration:** `component/otel/`

### 🕐 Tempo (Distributed Tracing)
- **Purpose:** Store and query distributed traces
- **Access:** http://localhost:3200
- **Configuration:** `component/tempo/`

### 📊 Grafana (Visualization)
- **Purpose:** Unified dashboard for logs, metrics, and traces
- **Access:** http://localhost:31001
- **Provisioning:** Automatic data source configuration

## 🐍 Application Integration

### Python Logging (Loki)
```python
from infrastructure.monitoring.component.loki.python_logger_example import setup_logging

# For development
setup_logging('infrastructure/monitoring/component/grafana/storage/development/myapp/app.log')

import logging
logging.info("This log will appear in Grafana!")
```

### OpenTelemetry (Traces & Metrics)
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.grpc.trace_exporter import OTLPSpanExporter

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to OTEL Collector
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
trace.get_tracer_provider().add_span_processor(span_processor)

# Use in your code
with tracer.start_as_current_span("my_operation"):
    # Your application logic here
    pass
```

### Prometheus Metrics
```python
from prometheus_client import start_http_server, Counter, Histogram

# Start metrics server
start_http_server(8000)

# Define metrics
requests_total = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Use in your code
@requests_total.count_exceptions()
def my_endpoint():
    with request_duration.time():
        # Your endpoint logic
        pass
```

## 🔍 Grafana Queries

### Logs (Loki)
```logql
{job="python-app"}                           # All logs
{job="python-app", env="development"}       # Development logs only
{job="python-app"} |= "error"               # Error logs only
```

### Metrics (Prometheus)
```promql
up{}                                        # Service uptime
rate(requests_total[5m])                    # Request rate
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))  # 95th percentile latency
```

### Traces (Tempo)
```tempo
{ service.name = "my-service" }             # Traces for specific service
{ span.name = "my_operation" }              # Specific operation traces
```

## 🛠️ Management

### Start All Services
```bash
./setup-observability.sh
```

### Start Individual Services
```bash
cd component/loki && docker compose -f logger-loki-compose.yaml up -d
cd ../prometheus && docker compose -f prometheus-compose.yaml up -d
cd ../otel && docker compose -f otel-collector-compose.yaml up -d
cd ../tempo && docker compose -f tempo-compose.yaml up -d
cd ../grafana && docker compose -f dashboard-grafana-compose.yaml up -d
```

### Stop All Services
```bash
cd component/loki && docker compose -f logger-loki-compose.yaml down
cd ../prometheus && docker compose -f prometheus-compose.yaml down
cd ../otel && docker compose -f otel-collector-compose.yaml down
cd ../tempo && docker compose -f tempo-compose.yaml down
cd ../grafana && docker compose -f dashboard-grafana-compose.yaml down
```

### View Logs
```bash
# All services
docker compose -f component/*/docker-compose.yaml logs -f

# Specific service
docker logs loki
docker logs prometheus
docker logs otel-collector
```

## 🔒 Security Considerations

- Change default Grafana password in production
- Use proper TLS/SSL certificates
- Configure authentication for exposed endpoints
- Implement rate limiting for metrics endpoints
- Use secrets management for sensitive configuration

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting:** Check Docker daemon and available resources
2. **Grafana datasource errors:** Verify service discovery and network connectivity
3. **No logs/metrics appearing:** Check application instrumentation and OTEL Collector configuration
4. **Performance issues:** Monitor resource usage and adjust retention policies

### Debug Commands

```bash
# Check service health
curl http://localhost:31090/ready  # Loki
curl http://localhost:9090/-/ready # Prometheus
curl http://localhost:3200/ready   # Tempo

# View service logs
docker logs loki --tail 50
docker logs prometheus --tail 50
docker logs otel-collector --tail 50

# Check network connectivity
docker exec grafana-development curl http://loki:3100/ready
```

## 📚 Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)

---

**🎯 Your complete observability stack is ready for production use!**
