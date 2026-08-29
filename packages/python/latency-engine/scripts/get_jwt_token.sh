#!/usr/bin/env bash
set -euo pipefail

AUTH_URL="${AUTH_URL:-http://localhost:3001/api/v1/auth/sign-in}"
EMAIL="${EMAIL:-jaydeep@gmail.com}"
PASSWORD="${PASSWORD:-Password12345!}"
LATENCY_HOST="${LATENCY_HOST:-http://localhost:8003}"

echo "[Auth] Fetching JWT Bearer token from $AUTH_URL for $EMAIL..."
RESPONSE=$(curl -s -X POST "$AUTH_URL" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('token', ''))")

if [ -z "$TOKEN" ]; then
  echo "[Error] Failed to fetch token. Response:"
  echo "$RESPONSE"
  exit 1
fi

echo "[Auth] Token acquired successfully!"
echo "TOKEN: $TOKEN"
echo ""

echo "=== 1. Testing GET /v1/latency/percentiles ==="
curl -s -X GET "$LATENCY_HOST/v1/latency/percentiles?model=gpt-4o&hour_of_day=14&quantiles=0.50,0.95,0.99" \
  -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 2. Testing GET /v1/latency/slo ==="
curl -s -X GET "$LATENCY_HOST/v1/latency/slo?model=gpt-4o&endpoint=%2Fv1%2Fchat%2Fcompletions" \
  -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 3. Testing GET /v1/latency/attribution ==="
curl -s -X GET "$LATENCY_HOST/v1/latency/attribution?model=gpt-4o&hour=2026-08-29" \
  -H "Authorization: Bearer $TOKEN"
echo ""

echo "=== 4. Testing GET /v1/latency/baseline ==="
curl -s -X GET "$LATENCY_HOST/v1/latency/baseline?model=gpt-4o&hour_of_day=14&days=7" \
  -H "Authorization: Bearer $TOKEN"
echo ""
