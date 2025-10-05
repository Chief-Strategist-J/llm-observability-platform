# Database Services

Shared Neo4j and Qdrant database setup.

## Quick Start

```bash
# Start databases only
docker-compose -f docker-compose.databases.yml --profile databases up -d

# Start with kg-service
docker-compose -f docker-compose.databases.yml --profile databases -f ../../service/kg-service/docker-compose.yml up -d

# Start with rag-service
docker-compose -f docker-compose.databases.yml --profile databases -f ../../service/rag-service/docker-compose.yml up -d
```

## Environment Variables

- `NEO4J_AUTH`: Neo4j credentials (default: neo4j/Scaibu@123)
- `DATABASE_SUBNET`: Network subnet (default: 172.26.0.0/16)

See CHANGELOG.md for detailed changes.
