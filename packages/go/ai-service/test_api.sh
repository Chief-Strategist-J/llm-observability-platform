#!/bin/bash
set -e

echo "Starting local integration verification..."

export PORT=8080
export CF_ACCOUNT_ID="local-account"
export CF_API_TOKEN="local-token"

./bin/ai-service &
PID=$!

cleanup() {
    echo "Stopping AI Service server (PID: $PID)..."
    kill $PID || true
    wait $PID 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for server to start..."
sleep 2

echo "----------------------------------------"
echo "1. Testing GET /api/v1/models"
echo "----------------------------------------"
curl -s -f http://localhost:8080/api/v1/models | jq .

echo "----------------------------------------"
echo "2. Testing POST /api/v1/chat"
echo "----------------------------------------"
curl -s -f -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "@cf/meta/llama-3.1-8b-instruct",
    "messages": [
      {"role": "user", "content": "Explain Hexagonal Architecture in Go."}
    ]
  }' | jq .

echo "----------------------------------------"
echo "3. Testing POST /api/v1/chat/persistent (Turn 1)"
echo "----------------------------------------"
curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_999",
    "message": "My name is John Doe.",
    "model": "@cf/meta/llama-3.1-8b-instruct"
  }' | jq .

echo "----------------------------------------"
echo "4. Testing POST /api/v1/chat/persistent (Turn 2 - Context Retrieval)"
echo "----------------------------------------"
curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_999",
    "message": "What is my name?",
    "model": "@cf/meta/llama-3.1-8b-instruct"
  }' | jq .

echo "----------------------------------------"
echo "Integration verification completed successfully!"
