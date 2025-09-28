#!/bin/bash
echo "Stopping RAG service..."
docker compose --profile active down
echo "Service stopped"
