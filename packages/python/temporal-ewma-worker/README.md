# Temporal EWMA Worker

Temporal worker package for scheduled EWMA baseline updates and cost anomaly detection.

## Architecture

This worker is built following the Ports and Adapters (Hexagonal) architecture:
- **Domain/Core**: Contains the pure EWMA computation logic and the deterministic workflow definition.
- **Ports**: Protocol definitions for dependencies (ClickHouse, Redis, Postgres, Kafka).
- **Adapters**: Concrete implementations for the databases and message bus.
- **Activities**: Functions executing actual side effects and I/O using the adapters.

## Features

- **F-C-07**: Per-(service, model, hour_of_week) EWMA updates.
- **F-C-08**: Anomaly checking (current cost > 3x EWMA baseline).
- **F-C-09**: Cold start seeding using model-wide average cost.

## Setup & Running

Copy `.env.example` to `.env` and configure accordingly, then run:

```bash
./scripts/run.sh
```
