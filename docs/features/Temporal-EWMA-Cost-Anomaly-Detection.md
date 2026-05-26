# Temporal EWMA & Cost Anomaly Detection

The `temporal-ewma-worker` is a decoupled microservice designed to periodically compute Exponentially Weighted Moving Average (EWMA) baselines for LLM usage costs and detect anomalous cost spikes. 

It runs a FastAPI management server alongside a Temporal worker within a single container.

---

## baseline Computation & Anomaly Flow

```
[Hourly Cron Trigger (0 * * * *)]
└── EwmaBaselineUpdate Workflow Starts
    │
    └── Activity: fetch_active_pairs() (last 7 days active pairs)
        │
        └── Loop over active (service, model) pairs concurrently:
            │
            ├── Activity: get_baseline(service, model, hour_of_week)
            │   ├── Existing Baseline NOT found (Cold Start)
            │   │   ├── Activity: fetch_global_model_avg(model)
            │   │   └── Seed EWMA baseline value = Global Model Average
            │   └── Existing Baseline found (Warm Status)
            │       ├── Activity: fetch_cost_history(service, model, hour_of_week) (last 4 weeks)
            │       └── Compute EWMA baseline value using α=0.1
            │
            ├── Activity: fetch_current_cost_1h(service, model)
            ├── Activity: upsert_baseline(EwmaRecord)
            ├── Write updated EWMA value to Redis Cache
            │   └── Key: ewma:cost:{service}:{model}:{hour_of_week}
            │
            └── Decision: Is Cost_current > (3 * EWMA_baseline)?
                ├── YES (Anomaly Detected)
                │   ├── Activity: fetch_cost_by_cluster_1h(service, model)
                │   └── Activity: publish_anomaly_alert(AnomalyPayload) -> Kafka topic
                └── NO (Normal State)
                    └── Do nothing
```

---

## Redis Baseline Cache Path

Baselines are pushed directly to Redis Cache for instant retrieval by the real-time ingestion/gateway layers:

* **Key Format**: `ewma:cost:{service}:{model}:{hour_of_week}`
* **Hour of Week (`hour_of_week`)**: An integer from `0` to `167` representing the hour starting from Monday 00:00 (0) to Sunday 23:00 (167).

---

## Standalone Setup & Execution

An end-user can install and run this package individually by following these steps:

### 1. Install the package and dependencies:
```bash
pip install -e packages/python/temporal-ewma-worker
```

### 2. Spin up local infrastructure:
This runs ClickHouse, PostgreSQL, Redis, Kafka, and Temporal:
```bash
docker compose -f packages/python/temporal-ewma-worker/deploy/docker/docker-compose.yaml up -d
```

### 3. Configure the environment:
```bash
cp packages/python/temporal-ewma-worker/.env.example packages/python/temporal-ewma-worker/.env
```

### 4. Apply database migrations:
Apply SQL migration schemas to PostgreSQL:
```bash
./packages/python/temporal-ewma-worker/scripts/migrate.sh up
```

### 5. Run test verification:
Verify configuration and end-to-end integration flows:
```bash
./packages/python/temporal-ewma-worker/scripts/test.sh
```

### 6. Start the Worker & FastAPI Server:
Start both services concurrently inside a single process:
```bash
./packages/python/temporal-ewma-worker/scripts/run.sh
```

---

## REST Management API

The worker exposes a REST management layer on port `8000`:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | GET | Retrieve worker configuration and running environment status |
| `/trigger` | POST | Trigger the EWMA baseline calculation workflow on-demand |

### Trigger Baseline Calculation On-Demand:
```bash
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{"force_hour": 42}'
```

---

## Next Steps

- [REST Management API](../reference/REST-Management-API.md) - Learn more about the core management endpoints.
- [Config Files Reference](../reference/Config-Files-Reference.md) - Learn how model prices and infrastructure endpoints are configured.
