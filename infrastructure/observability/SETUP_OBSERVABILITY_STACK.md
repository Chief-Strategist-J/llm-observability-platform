# Setup Observability Stack

This guide describes how to deploy, configure, and use the full observability stack (Loki, Prometheus, Jaeger, Grafana, Alertmanager, OTEL Collector) using the Python automation framework.

## 1. Prerequisites

- **Python 3.10+** (in virtual environment)
- **Docker & Docker Compose**
- **Temporal Server** running locally
- **mkcert** (for SSL certificates)
- **sudo** access (for `/etc/hosts` updates)

## 2. Infrastructure Code Structure

- `infrastructure/observability/setup/`
  - `observability_stack_setup_workflow.py`: Main orchestration logic.
  - `observability_stack_setup_activities.py`: Network and docker activities.
  - `observability_stack_setup_worker.py`: Temporal worker.
  - `trigger_observability_stack_setup.py`: CLI trigger.
  - `config/`: Docker compose and service definition YAMLs.

## 3. Deployment Steps

### Step 1: Start Temporal Worker
The worker hosts the workflow and activities.
```bash
cd /home/j/live/dinesh/llm-chatbot-python
source .venv/bin/activate
python infrastructure/observability/setup/observability_stack_setup_worker.py
```
*Keep this terminal running.*

### Step 2: Trigger Setup
Run the trigger script to start the setup workflow.
```bash
python infrastructure/observability/setup/trigger_observability_stack_setup.py setup
```

## 4. How to Use the Observability Client

We provide a reusable Python client `observability_client.py` that handles OTLP export and API verification.

### collecting Logs
To send logs to Loki via OTLP:
```python
from observability_client import ObservabilityClient
client = ObservabilityClient()
client.log_info("User logged in", {"user.id": "123"})
client.log_error("Payment failed", {"error.code": "500"})
```

### Collecting Metrics
To send metrics to Prometheus via OTLP:
```python
# Increment a counter
client.increment_counter(1, {"status": "success"})
```

### Collecting Tracing
To send traces to Jaeger via OTLP:
```python
with client.tracer.start_as_current_span("checkout_process"):
    client.log_info("Processing checkout")
    # ... nested operations
```

### Creating Alerts
Alerts are defined in `infrastructure/observability/setup/config/alerting-rules.yml`.
Example rule:
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status="500"}[5m]) > 1
  for: 1m
```
To trigger the `TestAlert` (gauge > 5), use the client helper:
```python
client.trigger_test_alert(value=15, duration_sec=60)
```

## 5. Using APIs

You can programmatically verify data using the `ObservabilityVerifier` class in the client file, or using HTTP requests.

### Using Python Client API
```python
from observability_client import ObservabilityVerifier
verifier = ObservabilityVerifier(base_url="https://scaibu.grafana")

# Query Metrics
metrics = verifier.query_prometheus("test_counter_total")

# Query Logs
logs = verifier.query_loki('{job="observability-client"}')

# Query Alerts
alerts = verifier.check_alerts()
```

### Using cURL (HTTP API)
All services are exposed via Traefik on `127.0.1.1` (requires `/etc/hosts` mapping).

**Query Prometheus:**
```bash
curl -k -u admin:SuperSecret123! \
  "https://scaibu.grafana/api/datasources/proxy/uid/prometheus/api/v1/query?query=up"
```

**Query Loki:**
```bash
curl -G -k -u admin:SuperSecret123! \
  "https://scaibu.grafana/api/datasources/proxy/uid/loki/loki/api/v1/query_range" \
  --data-urlencode 'query={job="observability-client"}'
```

**Query Jaeger:**
```bash
curl -k -u admin:SuperSecret123! \
  "https://scaibu.grafana/api/datasources/proxy/uid/jaeger/api/traces?service=observability-client"
```

## 6. Accessing Dashboards
Access Grafana at [https://scaibu.grafana](https://scaibu.grafana).
Login: `admin` / `SuperSecret123!`
