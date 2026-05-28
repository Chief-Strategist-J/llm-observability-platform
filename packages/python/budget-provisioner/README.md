# Budget Provisioner Service

The `budget-provisioner` is an internal FastAPI REST service that manages user model rate limits and budgets. It persists budget configurations in PostgreSQL and propagates immediate invalidation signals to Redis.

## Value Proposition
- **Real-time Synchronization**: Invalidating Redis keys immediately ensures token buckets reload dynamically on the next API call.
- **Service-to-Service Security**: Protects internal routes with JWT-based S2S authentication.
- **Observability**: Exposes high-fidelity OpenTelemetry spans for CRUD transactions.

## Architecture

This package follows hexagonal architecture principles (Ports and Adapters):
- **Domain**: Definitions and invariants.
- **Ports**: Inward (API handlers) and Outward (DbPort, RedisPort).
- **Adapters**: Concrete implementations (PostgreSQL using Psycopg, Redis using redis-py).

## Dependencies
- **PostgreSQL**: Stores persistent budget configurations.
- **Redis**: Caches and coordinates token bucket states.
- **Python**: 3.12+ with FastAPI.

## Configuration (Environment Variables)
- `POSTGRES_DSN`: PostgreSQL connection DSN (e.g. `postgresql://postgres:postgres@localhost:5432/postgres`).
- `REDIS_URL`: Redis connection URL (e.g. `redis://localhost:6379/0`).
- `INTERNAL_JWT_SECRET`: Secret key used to validate service-to-service Bearer tokens.
- `PORT`: Service port (default: `8001`).
- `HOST`: Service binding address (default: `0.0.0.0`).

## API Endpoints

All endpoints except `/health` require the `Authorization: Bearer <JWT>` header.

- **GET `/health`**: Returns JSON `{"status": "healthy", "service": "budget-provisioner"}`.
- **POST `/budgets/{user_id}/{model}`**: Creates or updates a budget.
  - Body:
    ```json
    {
      "max_budget": 100.0,
      "window_size_secs": 900,
      "initial_fill_fraction": 0.1
    }
    ```
- **GET `/budgets/{user_id}`**: Lists all budgets defined for the specified user.
- **DELETE `/budgets/{user_id}/{model}`**: Deletes a budget configuration.
- **GET `/budgets/{user_id}/{model}/status`**: Returns the remaining tokens and active burn rate from Redis.

## Observability & Tracing

This microservice has comprehensive, high-fidelity OpenTelemetry tracing spans wrapping every handler, domain service, and infrastructure adapter:

### Span Hierarchy

1. **POST `/budgets/{user_id}/{model}`**:
   - `budget_handler.create_or_update_budget` (Root API Span)
     - `budget_service.create_or_update_budget` (Domain Service Span)
       - `postgres_adapter.upsert_budget` (Postgres Adapter DB Span)
       - `redis_adapter.invalidate_budget_cache` (Redis Invalidation Span)

2. **GET `/budgets/{user_id}`**:
   - `budget_handler.list_budgets` (Root API Span)
     - `budget_service.list_budgets` (Domain Service Span)
       - `postgres_adapter.list_budgets` (Postgres Query Span)

3. **DELETE `/budgets/{user_id}/{model}`**:
   - `budget_handler.delete_budget` (Root API Span)
     - `budget_service.delete_budget` (Domain Service Span)
       - `postgres_adapter.delete_budget` (Postgres Delete Span)
       - `redis_adapter.invalidate_budget_cache` (Redis Invalidation Span)

4. **GET `/budgets/{user_id}/{model}/status`**:
   - `budget_handler.get_budget_status` (Root API Span)
     - `budget_service.get_budget_status` (Domain Service Span)
       - `postgres_adapter.get_budget` (Postgres Query Span)
       - `redis_adapter.get_token_bucket_status` (Redis Status Query Span)

## Docker Deployment

Build the docker image:
```bash
docker build -t chiefj/budget-provisioner:latest -f build/Dockerfile .
```

Run using Docker Compose:
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```

## Running Tests
Run unit, integration, and contract tests:
```bash
pytest tests/
```
