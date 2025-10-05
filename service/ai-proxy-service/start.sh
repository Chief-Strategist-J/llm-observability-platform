#!/bin/bash
set -e
docker compose down 2>/dev/null || true
docker compose up -d --build
sleep 5
echo "API: http://localhost:8000/docs"
