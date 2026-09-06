#!/bin/bash
set -e

if [ -z "$CF_ACCOUNT_ID" ] || [ -z "$CF_API_TOKEN" ]; then
    echo "Error: CF_ACCOUNT_ID and CF_API_TOKEN must be set in environment" >&2
    exit 1
fi

export PORT=8080

./bin/ai-service &
PID=$!

cleanup() {
    kill $PID || true
    wait $PID 2>/dev/null || true
}
trap cleanup EXIT

sleep 2

curl -s -f http://localhost:8080/api/v1/models | jq . | head -n 30 || curl -s http://localhost:8080/api/v1/models | jq .

curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "live_user_123",
    "message": "Hello Cloudflare! My favorite programming language is Go.",
    "model": "@cf/meta/llama-3-8b-instruct",
    "embedding_model": "@cf/baai/bge-small-en-v1.5"
  }' | jq .

curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "live_user_123",
    "message": "What is my favorite programming language?",
    "model": "@cf/meta/llama-3-8b-instruct",
    "embedding_model": "@cf/baai/bge-small-en-v1.5"
  }' | jq .
