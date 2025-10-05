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
