#!/bin/bash
echo "Starting RAG service..."
docker compose --profile active up -d
echo "Service started at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
