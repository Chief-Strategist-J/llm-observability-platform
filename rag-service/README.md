# RAG Service

Minimal RAG service with PDF processing and Qdrant vector database.

## Quick Start

```bash
# Start service
./start.sh

# Stop service
./stop.sh
```

## API Endpoints

1. **Upload PDF**: `POST /upload/pdf`
   - Upload PDF file for processing and embedding

2. **Search RAG**: `POST /search/rag`
   - Query: `{"query": "your question"}`
   - Returns answer with sources

## Access
- API: http://localhost:8000/docs
- Qdrant: http://localhost:6333/dashboard

## Usage

1. Start service with `./start.sh`
2. Upload PDF via `/upload/pdf`
3. Query via `/search/rag`
4. Stop service with `./stop.sh`
