#!/usr/bin/env bash
set -euo pipefail

# Generate unique valid UUIDs
SPAN_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
TRACE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

echo "1. Sending span to instrumentation API (span_id: $SPAN_ID)..."
curl -s -X POST http://localhost:8002/v1/spans \
  -H "Content-Type: application/json" \
  -d '{
    "span_id": "'"$SPAN_ID"'",
    "trace_id": "'"$TRACE_ID"'",
    "schema_version": 1,
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "test-service",
    "endpoint": "/v1/chat/completions",
    "environment": "dev",
    "prompt_tokens": 50,
    "completion_tokens": 30,
    "latency_ms_total": 500,
    "finish_reason": "stop",
    "cost_usd_micro": 15,
    "price_version": "v1",
    "token_count_method": "tiktoken",
    "is_sampled": true,
    "timestamp_utc": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'

echo -e "\n\n2. Producing quality score details to Kafka topic (llm.quality.scores)..."
docker exec -i docker-kafka-1 kafka-console-producer --topic llm.quality.scores --bootstrap-server kafka:29092 <<EOF
{"span_id": "$SPAN_ID", "trace_id": "$TRACE_ID", "model": "gpt-4o", "endpoint": "/v1/chat/completions", "prompt_type": "chat", "response_language": "en", "scores": {"coherence": 0.88, "toxicity": 0.05, "faithfulness": 0.95, "perplexity": 10.2}, "quality_flags": [], "scored_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")", "user_id": "test_user"}
EOF

echo -e "\nDone! A new span and quality score have been pushed."
echo "Check your metrics in Grafana at: http://localhost:3002/explore"
