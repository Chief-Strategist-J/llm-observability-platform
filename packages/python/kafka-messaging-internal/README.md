# Kafka Messaging Internal

A Python package for internal Kafka messaging operations following strict hexagonal architecture principles.

## Architecture

This package follows hexagonal architecture with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  REST Handlers │  │  FastAPI Router │  │  Middleware  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Event Processing│  │ Schema Registry │  │ DB Operations│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Port Interfaces│  │  Error Handling │  │  Utilities   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   PostgreSQL    │  │ Schema Registry │  │   Tracing    │ │
│  │     Adapter     │  │    Adapter      │  │   System     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Event Processing**: Store, query, and process Kafka events
- **Schema Registry**: Register, validate, and manage schemas
- **Database Operations**: Event storage and consumer offset management
- **OpenTelemetry Tracing**: Full observability with required span attributes
- **Contract-First API**: OpenAPI v1 specification with comprehensive testing

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (for event storage)
- Schema Registry (optional, for schema management)

### Installation

1. Clone the repository
2. Run the setup script:

```bash
./scripts/setup.sh
```

3. Configure environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:

```bash
./scripts/migrate.sh
```

5. Start the application:

```bash
./scripts/run.sh
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
POSTGRES_DSN=postgresql://user:password@localhost:5432/kafka_events

# Schema Registry
SCHEMA_REGISTRY_URL=http://localhost:8081

# Application
API_HOST=0.0.0.0
API_PORT=8000

# Tracing
OTEL_SERVICE_NAME=kafka-messaging-internal
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Spec: http://localhost:8000/openapi.json

## Development

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run specific test types
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh contract
./scripts/test.sh e2e
./scripts/test.sh performance

# Generate coverage report
./scripts/test.sh coverage
```

### Code Quality

```bash
# Setup pre-commit hooks (done by setup.sh)
pre-commit install

# Manual linting
ruff check src/
black src/
mypy src/
```

### Database Migrations

```bash
# Run pending migrations
./scripts/migrate.sh

# Check migration status
./scripts/migrate.sh status

# Rollback last migration
./scripts/migrate.sh rollback
```

## Architecture Rules

This package strictly follows these architectural rules:

### Layer Call Rules
- API → Feature/index (ONLY)
- Feature/service → Feature/repository (ONLY)
- Feature/repository → Infrastructure/adapters (via ports ONLY)
- Infrastructure/adapters → Vendor SDKs (ONLY)

### Package Isolation
- No cross-package imports
- Complete dependency isolation
- Self-contained deployment

### Port/Adapter Pattern
- All infrastructure dependencies implement port interfaces
- No direct vendor calls in business logic
- Adapter selection via DI container

### Tracing Requirements
- Root spans on all inbound requests
- Required attributes: service.name, service.version, deployment.env, host.name, feature.name, api.version
- Error recording with full context

### Migration Rules
- Numbered migration files (immutable)
- Corresponding rollback files
- Schema.lock file for tracking
- No manual database changes

## Project Structure

```
kafka-messaging-internal/
├── contracts/                 # API contracts (OpenAPI)
│   └── openapi/
│       └── v1.yaml
├── src/                       # Source code
│   ├── api/                   # API layer
│   │   └── rest/v1/
│   ├── features/               # Feature layer
│   │   ├── event-processing/
│   │   ├── schema-registry/
│   │   └── database-operations/
│   ├── shared/                 # Shared layer
│   │   ├── ports/             # Port interfaces
│   │   ├── errors/            # Error handling
│   │   ├── utils/             # Utilities
│   │   └── di/               # DI container
│   └── infra/                 # Infrastructure layer
│       ├── adapters/           # Adapters
│       └── tracing/           # Tracing system
├── database/                  # Database migrations
│   ├── migrations/
│   └── schema.lock
├── tests/                     # Test suite
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   └── performance/
├── scripts/                   # Utility scripts
├── pyproject.toml
├── .env.example
├── coupling-map.md
└── .port-registry
```

## API Endpoints

### Database Operations
- `POST /api/v1/database/events` - Store single event
- `GET /api/v1/database/events` - Query events
- `POST /api/v1/database/events/batch` - Store multiple events
- `GET /api/v1/database/offsets` - Get consumer offsets
- `POST /api/v1/database/offsets` - Update consumer offset
- `GET /api/v1/database/count` - Get event count
- `GET /api/v1/database/unprocessed` - Get unprocessed events
- `DELETE /api/v1/database/events/by-topic/{topic}` - Delete events by topic

### Schema Registry
- `POST /api/v1/schema-registry/schemas` - Register schema
- `GET /api/v1/schema-registry/schemas` - List subjects
- `GET /api/v1/schema-registry/schemas/{subject}` - Get schema
- `POST /api/v1/schema-registry/compatibility` - Check compatibility
- `PUT /api/v1/schema-registry/compatibility/{subject}` - Update compatibility
- `POST /api/v1/schema-registry/serialize` - Serialize data
- `POST /api/v1/schema-registry/deserialize` - Deserialize data

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/` - API information

## Contributing

1. Follow the architectural rules strictly
2. Run validation script before committing:
   ```bash
   ./scripts/validate.sh
   ```
3. Ensure all tests pass
4. Update documentation for any API changes

## License

MIT License - see LICENSE file for details.
