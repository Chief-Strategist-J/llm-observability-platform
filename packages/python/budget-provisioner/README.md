# Budget Provisioner Service

The `budget-provisioner` is an internal FastAPI REST microservice that exposes endpoints to create, retrieve, update, and delete budget configurations, and query current token bucket states.

---

## Why Use the Budget Provisioner?
- **Real-time Synchronization**: Invalidates Redis cache keys immediately on POST/DELETE, forcing downstream SDK calls to dynamically reload updated budget parameters.
- **Service-to-Service Security**: Protects CRUD endpoints using service-to-service JWT authentication.
- **Observability**: Exposes strict, high-fidelity OpenTelemetry trace spans and Prometheus invalidation metrics.
- **Hexagonal Architecture**: Isolates the domain and business rules from the underlying Postgres and Redis infrastructure adapters.

---

## Architecture Dependencies
Ensure these services are running in your environment:
1. **Redis Cache (>= 6.0)**: Coordinates active token bucket token counts and burn rates.
2. **PostgreSQL Database (>= 12)**: Persists long-term budget configuration schemas.

---

## Expected Results (Outputs)
Upon receiving API requests, the service:
- Inserts/updates configs in the PostgreSQL `budget_configs` table.
- Invalidates the Redis key `budget:{user_id}:{model}`.
- Increments the `budget_provisioner_invalidations_total` Prometheus counter.
- Returns JSON responses representing budget configs or active token bucket statuses.

---

## Folder Structure

```
.
├── build/
│   └── Dockerfile
├── contracts/
│   ├── changelog.md
│   └── openapi/
│       └── v1.yaml
├── database/
│   └── migrations/
│       ├── 0001_init.rollback.sql
│       └── 0001_init.sql
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── feature-registry.yaml
├── pyproject.toml
├── README.md
├── scripts/
│   ├── migrate.py
│   ├── migrate.sh
│   └── run.sh
├── src/
│   └── budget_provisioner/
│       ├── api/
│       │   ├── main.py
│       │   └── rest/
│       │       └── v1/
│       │           ├── handlers/
│       │           │   └── budgets.py
│       │           └── router.py
│       ├── config.py
│       ├── features/
│       │   └── budget_management/
│       │       ├── index.py
│       │       ├── repository.py
│       │       ├── service.py
│       │       └── types.py
│       ├── infra/
│       │   ├── adapters/
│       │   │   ├── metrics/
│       │   │   │   └── prometheus_adapter.py
│       │   │   ├── postgres/
│       │   │   │   └── postgres_adapter.py
│       │   │   └── redis/
│       │   │       └── redis_adapter.py
│       │   ├── auth.py
│       │   └── tracing/
│       │       └── tracer.py
│       └── shared/
│           ├── di/
│           │   └── container.py
│           ├── errors/
│           │   └── codes.py
│           └── ports/
│               ├── db_port.py
│               ├── metrics_port.py
│               └── redis_port.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── integration/
    │   └── test_api.py
    └── unit/
        ├── test_budget_service.py
        └── test_tracing.py
```

---

## Work Execution & Decision Flow

The decision trees detail the inner execution paths of the REST controller:

### 1. Create or Update Budget (`POST /budgets/{user_id}/{model}`)
```
[POST /budgets/{user_id}/{model} Request]
└── Authenticate Request (JWTAuthenticator)
    ├── Authentication Fails
    │   └── Return 401 Unauthorized
    └── Authentication Succeeds
        ├── 1. Upsert config in PostgreSQL (budget_configs table)
        ├── 2. Invalidate cache in Redis (DEL budget:{user_id}:{model})
        ├── 3. Increment Prometheus invalidation counter
        └── 4. Return 201 Created (or 200 OK if updating existing config)
```

### 2. Get Budget Status (`GET /budgets/{user_id}/{model}/status`)
```
[GET /budgets/{user_id}/{model}/status Request]
└── Authenticate Request (JWTAuthenticator)
    ├── Authentication Fails
    │   └── Return 401 Unauthorized
    └── Authentication Succeeds
        ├── 1. Query PostgreSQL for budget configuration
        │   ├── Config Not Found
        │   │   └── Return 404 Not Found
        │   └── Config Found (Proceed)
        │       └── 2. Query Redis for active token bucket status
        │           ├── Redis Key Exists
        │           │   └── Return tokens_remaining and burn_rate from Redis
        │           └── Redis Key Missing (Cold state)
        │               └── Return calculated initial state from PostgreSQL config
```

---

## Sequencing & Dependency Map

Services and scripts should be initialized in this sequence:

```
[Step 1: Spin Up Containers] -> [Step 2: Database Migration] -> [Step 3: Verification] -> [Step 4: Launch REST Service]
  • Postgres (5432)            • ./scripts/migrate.sh          • pytest tests/         • python -m budget_provisioner.api.main
  • Redis (6379)
```

---

## Setup & Execution

### 1. Configure Python Environment
Create a virtual environment and install packages:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Run Database Migrations
Apply PostgreSQL database schema migrations:
```bash
./scripts/migrate.sh
```

### 3. Run Verification Tests
Verify all API routes, core services, and tracing:
```bash
pytest tests/
```

### 4. Start the Service Locally
Launch the FastAPI development application server:
```bash
python -m budget_provisioner.api.main
```

---

## Observability & Tracing

The microservice emits OpenTelemetry tracing spans that correlate REST handlers with database queries and Redis calls.

### Tracing Span Hierarchy
- **`budget_handler.create_or_update_budget`** (Root span)
  - `budget_service.create_or_update_budget`
    - `postgres_adapter.upsert_budget`
    - `redis_adapter.invalidate_budget_cache`
- **`budget_handler.list_budgets`** (Root span)
  - `budget_service.list_budgets`
    - `postgres_adapter.list_budgets`
- **`budget_handler.delete_budget`** (Root span)
  - `budget_service.delete_budget`
    - `postgres_adapter.delete_budget`
    - `redis_adapter.invalidate_budget_cache`
- **`budget_handler.get_budget_status`** (Root span)
  - `budget_service.get_budget_status`
    - `postgres_adapter.get_budget`
    - `redis_adapter.get_token_bucket_status`

---

## Docker Deployment

### Build the Image
To build the Docker container:
```bash
docker build -f build/Dockerfile -t chiefj/budget-provisioner:latest .
```

### Deploy using Docker Compose
Orchestrate Postgres, Redis, Prometheus, and the FastAPI application:
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```

---

## End-User Usage Guide

### 1. Infrastructure Connection Configuration (Environment Variables)

Configure the microservice using the following environment variables:

| Variable | Description | Default / Example Value |
| :--- | :--- | :--- |
| **`HOST`** | Port binding address | `0.0.0.0` |
| **`PORT`** | Service listening port | `8001` |
| **`POSTGRES_DSN`** | PostgreSQL connection DSN string | `postgresql://postgres:postgres@localhost:5432/postgres` |
| **`REDIS_URL`** | Redis connection URL string | `redis://localhost:6379/0` |
| **`INTERNAL_JWT_SECRET`** | Secret key for validating incoming S2S JWT tokens | `super-secret-key-change-me-in-prod` |
| **`OTEL_EXPORTER_OTLP_ENDPOINT`** | OTLP collector collector endpoint | `http://localhost:4317` |
| **`OTEL_SERVICE_NAME`** | OpenTelemetry service name identifier | `budget-provisioner` |

#### Run via Docker CLI:
```bash
docker run -d \
  --name budget-provisioner \
  -e POSTGRES_DSN="postgresql://postgres:postgres@db-host:5432/postgres" \
  -e REDIS_URL="redis://redis-host:6379/0" \
  -e INTERNAL_JWT_SECRET="production-s2s-secret-key" \
  -p 8001:8001 \
  chiefj/budget-provisioner:latest
```

---

### 2. Interacting with API Endpoints

Make requests to the REST API by supplying a valid S2S JWT in the Authorization header.

#### Create or Update a Budget (`POST`)
```bash
curl -X POST http://localhost:8001/budgets/user_12345/gpt-4-turbo \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "max_budget": 250.0,
    "window_size_secs": 900,
    "initial_fill_fraction": 0.2
  }'
```

#### List Budgets for a User (`GET`)
```bash
curl -X GET http://localhost:8001/budgets/user_12345 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Query Active Token Bucket Status (`GET`)
```bash
curl -X GET http://localhost:8001/budgets/user_12345/gpt-4-turbo/status \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Delete Budget Config (`DELETE`)
```bash
curl -X DELETE http://localhost:8001/budgets/user_12345/gpt-4-turbo \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 3. Programmatic Usage in Python

Initialize ports and services directly in your Python code:

```python
from budget_provisioner.infra.adapters.postgres.postgres_adapter import PostgresAdapter
from budget_provisioner.infra.adapters.redis.redis_adapter import RedisAdapter
from budget_provisioner.infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from budget_provisioner.features.budget_management.service import BudgetManagementService

# 1. Instantiate the infrastructure adapters
db_port = PostgresAdapter("postgresql://postgres:postgres@localhost:5432/postgres")
redis_port = RedisAdapter("redis://localhost:6379/0")
metrics_port = PrometheusAdapter()

# 2. Inject ports into the domain service layer
service = BudgetManagementService(
    db_port=db_port,
    redis_port=redis_port,
    metrics_port=metrics_port
)

# 3. Invoke domain operations directly
config = service.create_or_update_budget(
    user_id="user_12345",
    model="gpt-4-turbo",
    max_budget=250.0,
    window_size_secs=900,
    initial_fill_fraction=0.2
)
print(f"Upserted budget config for {config.user_id} and model {config.model}")
```
