# Latency Baseline Worker

Temporal scheduled workflow worker for:
- Hourly latency metrics checkpointing from Redis DDSketches to ClickHouse `latency_checkpoints`.
- TTFT regression alert checking (`alerts.latency.ttft_regression` on Kafka) and baseline tracking in Redis.
- Active metric sketch rotation and health verification.

## System Data Flow Diagram

```text
       [ Redis DDSketch Keys ] ────────── (Reads ttft & total latency sketches)
                  │
                  ▼
      [ latency-baseline-worker ] (Temporal Scheduled Workflow: LatencyBaselineWorkflow)
            │                  │
            │ (F-L-11)         │ (F-L-12)
            │ Hourly           │ After Checkpoint Write
            │                  │
            ▼                  ▼
  [ ClickHouse: latency_checkpoints ]   [ Kafka: alerts.latency.ttft_regression ]
  Upserts model checkpoints by day+hour  Produces regression alert JSON messages
            │
            ▼
  [ Redis Baseline Keys ]
  Stores computed baseline_p99_ttft values
```

### Detailed Flow Logic:

#### 1. Hourly DDSketch Checkpoint (`F-L-11`)
*   Identifies active `(model, hour_of_day)` pairs by scanning `sketch:ttft:*` keys in Redis.
*   For each pair:
    *   Fetches the TTFT sketch `sketch:ttft:{model}:{hour_of_day}`.
    *   Fetches all corresponding total latency endpoint sketches `sketch:total:{model}:{endpoint}:{hour_of_day}`.
    *   Extracts quantiles (`p50`, `p95`, `p99`) and `sample_count` (`sketch.count`) from each sketch.
    *   Sums up the SLO error counters `slo:errors:{model}:{endpoint}:{minute_bucket}` for the entire hour.
    *   Upserts the data points to the ClickHouse `latency_checkpoints` table.

#### 2. TTFT Regression Check (`F-L-12`)
*   After the checkpoint write:
    *   Queries `p99_ttft_ms` history for the same model, endpoint, and hour of day over the last 7 days from ClickHouse.
    *   Computes `baseline_p99_ttft = median(last 7 values)`.
    *   Saves the computed baseline to Redis (`baseline:p99_ttft:{model}:{endpoint}:{hour_of_day}`).
    *   If `current_p99 > 2 * baseline_p99_ttft` and `sample_count >= 30`:
        *   Checks for cold starts (suppresses alerts if there are fewer than 7 prior historical data points).
        *   Produces a JSON alert to the `alerts.latency.ttft_regression` Kafka topic.

#### 3. Sketch Rotation (`F-L-13`)
*   On each hourly run, verifies that expected sketch keys exist in Redis for the current and prior hour.
*   If keys are missing (latency-engine was down), logs `sketch_missing_total{model, hour}` without crashing (leaving a natural gap in ClickHouse).

## Docker Operations

### Building the Image
You can build the Docker image locally:
```bash
docker build -t chiefj/latency-baseline-worker:latest -f build/Dockerfile .
```

### Running the Stack
To launch the worker alongside dedicated postgres, clickhouse, redis, and temporal containers:
```bash
cd deploy/docker
docker compose up -d --build
```

## Configuration (Environment Variables)
The worker can be configured using the following environment variables:
| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `TEMPORAL_HOST` | Temporal server address | `localhost:7239` |
| `TEMPORAL_NAMESPACE` | Temporal namespace | `default` |
| `TEMPORAL_TASK_QUEUE` | Temporal task queue name | `latency-baseline-tasks` |
| `CLICKHOUSE_HOST` | ClickHouse host | `localhost` |
| `CLICKHOUSE_PORT` | ClickHouse HTTP port | `8129` |
| `CLICKHOUSE_USERNAME` | ClickHouse username | `default` |
| `CLICKHOUSE_DATABASE` | ClickHouse database | `default` |
| `REDIS_URL` | Redis URL | `redis://localhost:6389/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap brokers | `localhost:9099` |
| `HEALTH_PORT` | HTTP port for the `/health` endpoint | `8003` |

## Local Testing
To execute the complete unit test suite locally:
```bash
./scripts/test.sh
```

## Realtime SSE Client Usage

The worker includes a dedicated realtime Server-Sent Events (SSE) subsystem to push structured status updates during Activity execution to any configured SSE Gateway (preserving `Last-Event-ID` across connection drops).

### Guidelines
* **Rule:** Always call `realtime/` from **Activities only**; calling from Workflows breaks Temporal determinism.
* **Rule:** Inject the active Workflow ID, Run ID, and Activity attempt number into the SSE client at execution time (never read from global state).

### Basic Integration Example
Within a Temporal activity:

```python
from temporalio import activity
from realtime import ConnectionManager, SSEEvent, RetryConfig, RetryPolicy

@activity.defn
async def hourly_checkpoint(info) -> int:
    act_info = activity.info()
    
    # 1. Initialize Connection Manager
    config = RetryConfig(max_attempts=3, initial_delay=1.0)
    manager = ConnectionManager(policy=RetryPolicy(config))
    
    # 2. Establish Connection
    gateway_url = "http://localhost:8000/events"
    await manager.connect(gateway_url)
    
    # 3. Construct and Push Event
    event = SSEEvent(
        event_type="checkpoint_started",
        data={"model": "gpt-4", "hour": 14},
        workflow_id=act_info.workflow_id,
        run_id=act_info.workflow_run_id,
        attempt=act_info.attempt
    )
    
    manager.send_event(gateway_url, event)
    
    # 4. Clean disconnect
    manager.disconnect()
    
    return 1
```

