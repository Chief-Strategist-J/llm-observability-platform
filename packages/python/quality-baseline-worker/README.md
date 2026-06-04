# Quality Baseline Worker

Temporal scheduled workflow worker for:
- 7-day rolling baseline recomputation (authoritative hourly recalc) from PostgreSQL to Redis.
- Quality trend daily rollup to ClickHouse at 00:00 UTC.

## System Data Flow Diagram

```text
[ PostgreSQL: quality_scores ] ─── (Reads scores & flags from last 7 days)
               │
               ▼
   [ quality-baseline-worker ] (Temporal Scheduled Workflows)
         │               │
         │ (F-Q-09)      │ (F-Q-10)
         │ Hourly        │ Daily at 00:00 UTC
         │               │
         ▼               ▼
   [   Redis   ]   [ ClickHouse ] ──► [ Grafana Dashboards ]
  Overwrites drifted  Appends daily      Plots 30-day quality
  baseline averages   rollup metrics     trend performance
```

### Detailed Flow Logic:

#### 1. Rolling Baseline Recomputation (Hourly Flow — `F-Q-09`)
```text
  [PostgreSQL: quality_scores]
               │
               ▼ SELECT avg(composite_score), count(*) ... WHERE scored_at > now() - 7 days
     [recompute_baseline_scores] (Activity)
               │
               ▼ Return List[BaselineRecomputeResult]
     [write_redis_baselines] (Activity)
               │
               ▼ SET baseline:quality:{model}:{endpoint}:{prompt_type} -> average_score
            [Redis]
```

#### 2. Quality Trend Rollup (Daily Flow at 00:00 UTC — `F-Q-10`)
```text
  [PostgreSQL: quality_scores]
               │
               ▼ SELECT avg(composite_score), sum(cardinality(flags)), count(*) ... for yesterday
       [rollup_quality_trend] (Activity)
               │
               ▼ INSERT INTO quality_trend (rollup_date, model, endpoint, prompt_type, ...)
        [ClickHouse]
```

## Docker Operations

### Building the Image
You can build the Docker image locally using the provided script:
```bash
./scripts/deploy_docker.sh
```

### Running the Stack
To launch the worker alongside dedicated PostgreSQL, ClickHouse, Redis, and Temporal containers:
```bash
cd deploy/docker
docker compose up -d --build
```
