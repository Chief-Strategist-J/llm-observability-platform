# Architecture Overview

## Project Structure

This project follows a microservices architecture with shared infrastructure components.

### Services
- **ai-proxy-service**: LLM API proxy with multiple providers
- **kg-service**: Knowledge graph service using Neo4j
- **rag-service**: RAG service using Qdrant vector store
- **automation-n8n-service**: Workflow automation service

### Infrastructure
- **databases/**: Shared Neo4j and Qdrant databases
- **kafka/**: Event streaming for async communication
- **redis/**: Caching and session storage
- **monitoring/**: Prometheus and Grafana setup

### Communication
- **GraphQL**: Synchronous API queries and mutations
- **Kafka**: Asynchronous event-driven communication
- **Docker Profiles**: Conditional service activation

## Key Features
- Conditional activation (services only run when requested)
- Shared databases with isolation
- Event-driven architecture for scalability
- GraphQL APIs for flexible querying
- Comprehensive change tracking in CHANGELOG.md

## Getting Started
See individual service README files and infrastructure/databases/README.md for usage instructions.
