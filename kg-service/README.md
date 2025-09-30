# Knowledge Graph SDK

Scalable Knowledge Graph service with advanced reasoning, memory layer, and entity extraction.

## 🚀 Quick Start

```bash
cd kg-service
./start.sh
```

## 📡 Endpoints

- API Docs: http://localhost:8002/docs
- Neo4j Browser: http://localhost:7474 (neo4j/changeme123)
- Health: http://localhost:8002/health

## 🔧 Usage

### Ingest Content
```bash
curl -X POST http://localhost:8002/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here",
    "source_id": "doc_001"
  }'
```

### Query
```bash
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here"}'
```

### Get Stats
```bash
curl http://localhost:8002/stats
```

## 🛑 Management

```bash
./stop.sh    # Stop services
./clean.sh   # Clean all data
```

## 📁 Structure

```
kg-service/
├── core/             # Business logic
│   ├── domain/       # Models
│   ├── ports/        # Interfaces
│   └── usecases/     # Use cases
├── adapters/         # Implementations
│   ├── graph_store/  # Neo4j
│   ├── embedding_model/
│   ├── chunking/
│   ├── entity_extractor/
│   └── memory_store/
├── api/              # FastAPI
└── config/           # Configuration
```
