# Embedding Service

Vector embedding microservice with Qdrant backend.

## 📁 Structure

```
embedding-service/
├── data/qdrant/                 # Persistent storage
├── api/routes/                  # FastAPI routes
├── core/                        # Core configuration & models
├── services/                    # Business logic
├── handlers/                    # Request processing
├── utils/                       # Helper functions
└── tests/                       # Test suites
```

## 🚀 Quick Start

```bash
# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# Initialize collection
curl -X POST http://localhost:8000/api/v1/collections/init

# Add data
curl -X POST http://localhost:8000/api/v1/collections/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "1", "text": "Machine learning is fascinating", "payload": {"category": "tech"}},
      {"id": "2", "text": "Deep learning models are powerful", "payload": {"category": "ai"}}
    ]
  }'

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "limit": 5}'
```

## 🔧 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# Run tests
pytest tests/
```

## 📊 API Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/collections/init` - Initialize default collection
- `POST /api/v1/collections/create` - Create new collection
- `POST /api/v1/collections/upsert` - Add/update items
- `POST /api/v1/embed` - Generate text embedding
- `POST /api/v1/search` - Search similar items

## 🌐 Access

- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard
