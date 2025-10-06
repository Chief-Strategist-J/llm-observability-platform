# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Shared database setup with Neo4j and Qdrant in `infrastructure/databases/`
- Profile-based conditional activation for databases using `--profile databases`
- Isolated `database-network` for security
- Docker volumes for data persistence (`neo4j_data`, `qdrant_storage`, `qdrant_temp`)

### Changed
- Moved Neo4j and Qdrant from service-specific docker-compose files to shared `infrastructure/databases/docker-compose.databases.yml`
- Updated `docker-compose.yml` to remove Neo4j service definition
- Updated `service/kg-service/docker-compose.yml` to depend on shared Neo4j
- Updated `service/rag-service/docker-compose.yml` to depend on shared Qdrant
- Added environment variables for database configuration (`NEO4J_AUTH`, `DATABASE_SUBNET`)

### Removed
- Duplicate Neo4j configuration from main `docker-compose.yml`
- Duplicate Qdrant configuration from `service/rag-service/docker-compose.yml`
- Duplicate Neo4j configuration from `service/kg-service/docker-compose.yml`

## [0.1.0] - 2024-10-05

### Added
- Initial project structure with ai-proxy-service, kg-service, rag-service, automation-n8n-service
- Basic docker-compose setup with Ollama
- Infrastructure folders for kafka, redis, monitoring, databases
- GraphQL integration folders in each service
- Kafka event handling folders in each service

### Infrastructure Setup
- Kafka cluster configuration in `infrastructure/kafka/`
- Redis cluster configuration in `infrastructure/redis/`
- Monitoring setup in `infrastructure/monitoring/`
- Database infrastructure in `infrastructure/databases/`

### Service Enhancements
- Added `api/graphql/` folder to each service for GraphQL API
- Added `events/` folder to each service for Kafka integration
- Consistent folder structure across all services for maintainability

## [Unreleased]

### Added
- Unified monitoring stack in `infrastructure/monitoring/` with Loki, Promtail, and Grafana
- Profile-based conditional activation for monitoring using `--profile monitoring`
- Centralized log collection from all Docker containers
- Isolated `monitoring-network` for monitoring services

### Changed
- Moved Grafana, Loki, and Promtail from `service/automation-n8n-service/` to shared `infrastructure/monitoring/`
- Updated Promtail configuration for dynamic container discovery across all services
- Updated `service/automation-n8n-service/compose.yaml` to remove monitoring services
- Simplified monitoring deployment with single compose file

### Removed
- Duplicate Grafana, Loki, and Promtail configurations from individual services
- Redundant monitoring volumes and networks in service-specific compose files


## [Unreleased]

### Added
- Shared routing infrastructure in `infrastructure/docker-compose.routing.yml` with Traefik
- Profile-based conditional activation for routing using `--profile routing`
- Isolated `routing-network` for proxy services
- Automatic SSL certificate management with Let's Encrypt

### Changed
- Moved Traefik configuration from `service/automation-n8n-service/` to shared `infrastructure/`
- Updated `service/automation-n8n-service/docker-compose.yml` to use shared Traefik
- Renamed `compose.yaml` to `docker-compose.yml` for better linting support
- Added routing documentation in `infrastructure/README.routing.md`

### Infrastructure Consolidation
- Centralized all shared services (databases, monitoring, routing) in `infrastructure/`
- Services now only contain their specific logic and Docker configurations
- Infrastructure services are shared across all application services
- Conditional activation prevents resource waste when services aren't needed


## [Unreleased]

### Added
- Lightweight Kafka infrastructure in `infrastructure/kafka/` using KRaft mode
- Profile-based conditional activation for Kafka using `--profile kafka`
- Single-node Kafka setup for development with easy scaling path
- Kafka documentation in `infrastructure/kafka/README.md`
- Environment variable configuration for Kafka networking

### Infrastructure Enhancement
- KRaft mode for faster startup and lower resource usage
- Proper listener configuration for container and host communication
- Health checks for Kafka broker availability
- Structured logging for Kafka services

### Event-Driven Architecture Foundation
- Ready for integration with all services (ai-proxy-service, kg-service, rag-service, automation-n8n-service)
- Supports multiple topics for different event types
- Easy to extend to multi-broker cluster for production scaling
