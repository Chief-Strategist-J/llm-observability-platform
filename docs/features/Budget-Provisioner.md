# Budget Provisioner

The `budget-provisioner` is an internal FastAPI REST service that manages user model rate limits and budgets. It persists budget configurations in PostgreSQL and propagates immediate invalidation signals to Redis.

## Core Operations

### API Endpoints
All endpoints except `/health` require the `Authorization: Bearer <JWT>` header:
- **POST `/budgets/{user_id}/{model}`**: Creates or updates a budget config.
- **GET `/budgets/{user_id}`**: Lists all budgets for a user.
- **DELETE `/budgets/{user_id}/{model}`**: Deletes a budget configuration.
- **GET `/budgets/{user_id}/{model}/status`**: Returns remaining tokens and active burn rate from Redis.

### Cache Invalidation Flow
Upon any POST or DELETE operation, the budget-provisioner immediately deletes the Redis key:
```
DEL budget:{user_id}:{model}
```
On the next SDK call, the bucket is reconstructed dynamically from PostgreSQL config with an initial fill fraction of 0.1.

## Observability & Tracing

The budget-provisioner service is fully instrumented with OpenTelemetry tracing spans:
- **REST Endpoints**: Root spans are named `budget_handler.<endpoint_name>`.
- **Domain Logic**: Spans are named `budget_service.<operation_name>`.
- **Adapters**: Concrete infrastructure adapters trace database queries and Redis invalidation commands.
