# API Documentation

## GraphQL APIs

Each service exposes a GraphQL API for synchronous operations.

### ai-proxy-service
- **Endpoint**: http://localhost:8001/graphql
- **Features**: LLM generation, text processing

### kg-service
- **Endpoint**: http://localhost:8002/graphql
- **Features**: Knowledge graph queries, entity management

### rag-service
- **Endpoint**: http://localhost:8000/graphql
- **Features**: Document search, vector similarity

### automation-n8n-service
- **Endpoint**: http://localhost:8003/graphql
- **Features**: Workflow management, automation triggers

## Event-Driven Communication

Services communicate asynchronously via Kafka topics:
- `user.requests`: User queries and requests
- `kg.enhancements`: Knowledge graph enhancements
- `rag.updates`: RAG search results
- `workflow.events`: Automation workflow triggers

## Usage Examples

### GraphQL Query
```graphql
query {
  knowledgeGraph(query: "machine learning") {
    entities {
      id
      content
    }
  }
}
```

### Kafka Event
```json
{
  "event_type": "user_request",
  "user_id": "123",
  "message": "What is AI?",
  "timestamp": "2024-01-01T00:00:00Z"
}
```
