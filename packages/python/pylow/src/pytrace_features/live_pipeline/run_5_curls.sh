#!/usr/bin/env bash
# run_5_curls.sh — Feed 5 distinct API formats into the pylow live pipeline
# This script is fully executable and acts as a source harness.

set -euo pipefail

# Find active pipeline ingestion pipe
if [ ! -f /tmp/pylow_pipeline_latest ]; then
  echo "Error: No active pipeline found. Please run 'pylow pipeline-run' first in another window."
  exit 1
fi

ACTIVE_DIR=$(cat /tmp/pylow_pipeline_latest)
INGEST_PIPE="$ACTIVE_DIR/pipes/ingest_in"

echo "=========================================================="
echo " Starting 5 Curl Sources feeding into $INGEST_PIPE"
echo "=========================================================="

# -------------------------------------------------------------
# SOURCE 1: Shopify Orders Webhook (Simulated)
# Payload format uses: order_id, total_price, currencyCode
# -------------------------------------------------------------
send_shopify_mock() {
  echo "🚀 Source 1: Sending Shopify webhook event..."
  curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "X-Signature-256: mock_signature" \
    -d '{
      "order_id": "shop_order_505",
      "total_price": "89.99",
      "currencyCode": "USD",
      "financial_status": "paid",
      "customer": {
        "email": "customer@shopify.com",
        "first_name": "Jane",
        "last_name": "Doe"
      }
    }' \
    http://localhost:9001 >/dev/null || true
}

# -------------------------------------------------------------
# SOURCE 2: Stripe Events Webhook (Simulated)
# Payload format uses: id, amount (in cents), currency, status
# -------------------------------------------------------------
send_stripe_mock() {
  echo "🚀 Source 2: Sending Stripe webhook event (High Value)..."
  curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "id": "ch_stripe_999",
      "amount": 150000,
      "currency": "usd",
      "status": "succeeded",
      "type": "charge.succeeded",
      "customer": {
        "id": "cus_stripe_111",
        "email": "stripe_buyer@gmail.com"
      }
    }' \
    http://localhost:9002 >/dev/null || true
}

# -------------------------------------------------------------
# SOURCE 3: Legacy API Transaction Poll (Simulated via curl pipe)
# Payload format uses: pay_id, value, state, currency_code
# -------------------------------------------------------------
poll_legacy_api() {
  echo "🚀 Source 3: Polling Legacy API (Returns different shape)..."
  # We fetch an HTTP dummy resource, parse it, and pipe it directly to ingest
  curl -s "https://httpbin.org/anything" \
    | jq -c --arg id "legacy_$(date +%s)" '{
      "pay_id": $id,
      "value": "45.00",
      "currency_code": "EUR",
      "state": "complete"
    }' >> "$INGEST_PIPE"
}

# -------------------------------------------------------------
# SOURCE 4: Failed Refund Event (Simulated)
# Payload format uses: transaction_id, amount, status
# -------------------------------------------------------------
send_failed_refund() {
  echo "🚀 Source 4: Simulating failed refund event..."
  curl -s "https://httpbin.org/anything" \
    | jq -c --arg id "ref_$(date +%s)" '{
      "transaction_id": $id,
      "amount": 12000,
      "currency": "USD",
      "status": "refunded",
      "metadata": {
        "refund_reason": "customer_request"
      }
    }' >> "$INGEST_PIPE"
}

# -------------------------------------------------------------
# SOURCE 5: Invalid/Malformed Payload (To demonstrate Dead Lettering)
# -------------------------------------------------------------
send_malformed_event() {
  echo "🚀 Source 5: Sending malformed payload (Missing currency)..."
  curl -s "https://httpbin.org/anything" \
    | jq -c --arg id "bad_$(date +%s)" '{
      "id": $id,
      "amount": "not-a-number",
      "currency": "INVALID_CURR",
      "status": "unknown"
    }' >> "$INGEST_PIPE"
}

# Execute all simulated curls once
send_shopify_mock
sleep 1
send_stripe_mock
sleep 1
poll_legacy_api
sleep 1
send_failed_refund
sleep 1
send_malformed_event

echo "=========================================================="
echo " All 5 sources sent to pipeline!"
echo " Monitor pipeline terminal or run 'pylow pipeline-tap route' to verify."
echo "=========================================================="
