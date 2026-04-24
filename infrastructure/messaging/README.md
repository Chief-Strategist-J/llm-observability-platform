# Messaging SDK

A comprehensive messaging SDK following Hexagonal Architecture (Ports and Adapters) principles for Kafka, Schema Registry, and database integration.

## Quick Start

### Simple Usage

```python
from infrastructure.messaging import create_postgres_sdk, ConsumerRecord

# Create SDK with PostgreSQL
sdk = create_postgres_sdk(
    dsn="postgresql://user:pass@localhost:5432/mydb",
    schema_registry_url="http://localhost:8081"
)

# Process events
record = ConsumerRecord(
    topic="my-topic",
    partition=0,
    offset=1,
    key="key1",
    value={"data": "test"},
    timestamp=1234567890
)
event_id = sdk.process_event(record)

# Register schema
schema_id = sdk.register_schema(
    subject="my-subject",
    schema='{"type":"record","name":"Test","fields":[]}',
    schema_type=SchemaType.AVRO
)

# Cleanup
sdk.close()
```

### Using Context Manager

```python
from infrastructure.messaging import create_mongodb_sdk

with create_mongodb_sdk(
    uri="mongodb://localhost:27017/",
    database_name="kafka_events"
) as sdk:
    sdk.process_event(record)
    # Automatically closes on exit
```

### Advanced Configuration

```python
from infrastructure.messaging import MessagingSDK, DatabaseConfig, SchemaRegistryConfig

db_config = DatabaseConfig(
    database_type="postgresql",
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    min_connections=2,
    max_connections=10
)

schema_config = SchemaRegistryConfig(
    url="http://localhost:8081",
    auth={"username": "user", "password": "pass"},
    compatibility="BACKWARD"
)

sdk = MessagingSDK(
    database_config=db_config,
    schema_registry_config=schema_config
)
```

## Available Factory Functions

- `create_postgres_sdk(dsn, schema_registry_url=None)` - Quick setup with PostgreSQL
- `create_mongodb_sdk(uri, database_name="kafka_events", schema_registry_url=None)` - Quick setup with MongoDB
- `create_schema_registry_sdk(url, auth=None)` - Schema Registry only

## SDK Methods

### Event Processing
- `process_event(record)` - Process single event
- `process_events_batch(records)` - Process multiple events

### Schema Registry
- `register_schema(subject, schema, schema_type)` - Register new schema
- `get_schema(subject, version=None)` - Get schema by subject
- `list_subjects()` - List all registered subjects

### Direct Access
- `sdk.database` - Direct access to database port
- `sdk.schema_registry` - Direct access to schema registry port
- `sdk.event_handler` - Direct access to event handler
- `sdk.schema_aware_handler` - Direct access to schema-aware handler

## Architecture

The SDK follows Hexagonal Architecture with three main layers:

### Domain Layer (`domain/`)
Business logic, ports (interfaces), and models with no external dependencies.

- **`ports/`** - Interface contracts (DatabasePort, SchemaRegistryPort)
- **`services/`** - Business services (EventHandler, SchemaAwareEventHandler)
- **`models/`** - Domain models and Pydantic schemas

### Infrastructure Layer (`infrastructure/`)
Concrete implementations of domain ports.

- **`adapters/`** - PostgreSQL, MongoDB, Schema Registry adapters
- **`messaging/`** - Kafka client implementations
- **`setup/`** - Docker configurations

### Application Layer (`application/`)
Orchestration and API endpoints.

- **`activities/`** - Temporal workflow activities
- **`api/`** - REST API endpoints

## Docker Setup

Start the Kafka stack with Schema Registry:

```bash
./infrastructure/messaging/infrastructure/setup/run-kafka.sh up
```

Services:
- Kafka: `localhost:9093`
- Kafka UI: `localhost:8082`
- Schema Registry: `localhost:8081`

## Key Principles

1. **Dependency Inversion**: Domain depends on abstractions, not implementations
2. **Infrastructure Independence**: Swap implementations (PostgreSQL ↔ MongoDB)
3. **Testability**: Test with mock implementations
4. **Single Responsibility**: Each component has one clear purpose
5. **Interface Segregation**: Focused and specific ports

## Directory Structure

```
infrastructure/messaging/
├── sdk.py                    # Main SDK client and factory functions
├── domain/                   # Business logic and interfaces
│   ├── ports/               # Interface contracts
│   ├── services/            # Business services
│   └── models/              # Domain models
├── infrastructure/           # External implementations
│   ├── adapters/            # Port implementations
│   ├── messaging/           # Kafka clients
│   └── setup/               # Docker configs
├── application/             # Orchestration and APIs
│   ├── activities/          # Temporal activities
│   └── api/                 # REST endpoints
├── utils/                   # Utility functions
├── tests/                   # Test suite
├── requirements.txt          # Python dependencies
├── setup_env.sh             # Virtual environment setup script
└── run_tests.sh             # Test execution script
```

## Testing

### Environment Setup

1. **Set up the virtual environment:**

```bash
cd infrastructure/messaging
./setup_env.sh
```

This will create a virtual environment in `venv/` and install core dependencies only.

**Optional dependency installation:**

To install optional dependencies for specific test categories:

```bash
# Install schema registry dependencies (for confluent-kafka tests)
./setup_env.sh --schema-registry

# Install application dependencies (for temporalio/fastapi tests)
./setup_env.sh --app

# Install all dependencies (core + optional)
./setup_env.sh --full
```

Or install manually after activating the venv:

```bash
source venv/bin/activate
pip install -r requirements-schema-registry.txt  # For schema registry tests
pip install -r requirements-app.txt            # For temporalio/fastapi tests
```

2. **Activate the virtual environment:**

```bash
source venv/bin/activate
```

### Running Tests

**Run all tests:**

```bash
./run_tests.sh
```

**Run specific test files:**

```bash
pytest tests/test_compression.py -v
pytest tests/test_serializers.py -v
pytest tests/test_partition_selector.py -v
pytest tests/test_database_port.py -v
pytest tests/test_schema_registry_port.py -v
pytest tests/test_event_handler.py -v
pytest tests/test_schema_aware_event_handler.py -v
pytest tests/test_schemas.py -v
pytest tests/test_postgres_adapter.py -v
pytest tests/test_mongodb_adapter.py -v
```

**Run with coverage:**

```bash
pytest tests/ --cov=. --cov-report=html
```

**Run excluding integration tests:**

```bash
pytest tests/ -m "not integration" -v
```

### Test Categories

- **Unit Tests:** Core domain logic, ports, services, and models
- **Adapter Tests:** PostgreSQL, MongoDB, and Schema Registry adapters
- **Utility Tests:** Compression, serializers, and partition selectors
- **Property-Based Tests:** Hypothesis-based tests for critical paths
- **Integration Tests:** End-to-end scenarios (requires running services)

### Dependencies

See `requirements.txt` for all required packages:

- **Core:** pydantic, python-dateutil
- **Database:** psycopg2-binary, pymongo
- **Schema Registry:** confluent-kafka, authlib, cachetools, fastavro, orjson, referencing
- **Testing:** pytest, pytest-asyncio, pytest-cov, hypothesis
- **Application:** temporalio, fastapi, uvicorn, httpx, pyyaml

### Deactivating the Environment

When done testing, deactivate the virtual environment:

```bash
deactivate
```
