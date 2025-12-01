# Observability Pipeline Tests

This directory contains standalone test scripts for validating the observability infrastructure without requiring Temporal workers.

## Available Tests

### Individual Pipeline Tests

Each test script can be run independently:

1. **`test_logs_pipeline.py`** - Tests Loki logs pipeline
   - Checks Loki health
   - Emits test log events
   - Verifies log ingestion
   - Supports cleanup with `--cleanup` flag

2. **`test_metrics_pipeline.py`** - Tests Prometheus metrics pipeline
   - Checks Prometheus health
   - Verifies Prometheus is operational
   - Supports cleanup with `--cleanup` flag

3. **`test_tracing_pipeline.py`** - Tests Tempo/Jaeger tracing pipeline
   - Checks Tempo and Jaeger health
   - Emits test traces
   - Verifies trace ingestion
   - Supports cleanup with `--cleanup` flag

### All Pipelines Test

**`test_all_pipelines.py`** - Runs all three pipeline tests sequentially and provides a comprehensive summary.

## Usage

### Run Individual Pipeline Test

```bash
# Logs pipeline
python infrastructure/tests/test_logs_pipeline.py

# Metrics pipeline  
python infrastructure/tests/test_metrics_pipeline.py

# Tracing pipeline
python infrastructure/tests/test_tracing_pipeline.py
```

### Run All Pipeline Tests

```bash
python infrastructure/tests/test_all_pipelines.py
```

### Cleanup After Testing

Individual cleanup:
```bash
python infrastructure/tests/test_logs_pipeline.py --cleanup
python infrastructure/tests/test_metrics_pipeline.py --cleanup
python infrastructure/tests/test_tracing_pipeline.py --cleanup
```

Cleanup all:
```bash
python infrastructure/tests/test_all_pipelines.py --cleanup
```

## Prerequisites

Before running tests, ensure the required services are running:

```bash
# Check running containers
docker ps | grep -E "(loki|prometheus|tempo|jaeger|grafana)"

# Verify services are healthy
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Network Isolation

All observability services use the `observability-network`, which is separate from the `temporal-network`. This ensures:
- Temporal services remain unaffected during testing
- No interference with Temporal UI
- Clean isolation between infrastructure components

## Cleanup Behavior

The cleanup functionality uses `YAMLContainerManager.delete()` with:
- `remove_volumes=True` - Removes all data volumes
- `remove_images=True` - Removes Docker images
- `remove_networks=False` - Preserves external networks (observability-network, temporal-network)

This ensures complete cleanup while maintaining network infrastructure for reuse.

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed
- `-1` - Test script error (e.g., missing dependencies)
