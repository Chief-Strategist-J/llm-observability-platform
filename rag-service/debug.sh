#!/bin/bash
echo "=== Qdrant ==="
docker logs qdrant-db --tail 50 || echo "qdrant-db not running"
echo ""
echo "=== API ==="
docker logs rag-api --tail 50 || echo "rag-api not running"
echo ""
echo "=== Status ==="
docker ps -a | grep -E "qdrant-db|rag-api" || echo "No containers"
