"""
Live Pipeline service.
Source-agnostic live transformation pipeline.
"""
import sys
import os
import subprocess
import time
import json
from typing import Optional
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

_COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "CYAN": "\033[96m",
    "MAGENTA": "\033[95m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}

def _c(color: str, text: str) -> str:
    return f"{_COLORS.get(color, '')}{text}{_COLORS['RESET']}"


class LivePipelineService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()
        self.base_dir = "/tmp/pylow_pipeline_workspace"

    def _prepare_scripts(self) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        stages_dir = os.path.join(self.base_dir, "stages")
        os.makedirs(stages_dir, exist_ok=True)

        # 1. pipeline.sh
        pipeline_sh = """#!/usr/bin/env bash
# pipeline.sh — source-agnostic live transformation pipeline
set -euo pipefail

PIPELINE_ID="pipeline_$$"
BASE_DIR="/tmp/$PIPELINE_ID"
PIPE_DIR="$BASE_DIR/pipes"
LOG_DIR="$BASE_DIR/logs"
STATE_DIR="$BASE_DIR/state"
STAGE_DIR="$BASE_DIR/stages"
DEAD_LETTER="$BASE_DIR/dead_letter.ndjson"
METRICS_FILE="$BASE_DIR/metrics.json"

mkdir -p "$PIPE_DIR" "$LOG_DIR" "$STATE_DIR" "$STAGE_DIR"
touch "$DEAD_LETTER"

# Save latest pipeline directory for debugging commands
echo "$BASE_DIR" > /tmp/pylow_pipeline_latest

# Copy JQ stages from workspace
cp -r /tmp/pylow_pipeline_workspace/stages/* "$STAGE_DIR/" 2>/dev/null || true

# global stage registry
declare -A STAGE_PIDS
declare -A STAGE_IN_PIPES
declare -A STAGE_OUT_PIPES

log() {
  local stage="$1" level="$2"
  shift 2
  echo "[$(date -u +%FT%TZ)] [$level] [stage=$stage] $*" \\
    >> "$LOG_DIR/${stage}.log"
}

metrics_inc() {
  local stage="$1" metric="$2"
  local file="$STATE_DIR/${stage}_${metric}.count"
  local current=$(cat "$file" 2>/dev/null || echo 0)
  echo $(( current + 1 )) > "$file"
}

metrics_report() {
  echo "=== pipeline metrics ==="
  for stage_metric in "$STATE_DIR"/*.count; do
    name=$(basename "$stage_metric" .count)
    count=$(cat "$stage_metric")
    echo "  $name: $count"
  done
}

# register a stage — creates its pipes and records it
register_stage() {
  local name="$1"
  local in_pipe="$PIPE_DIR/${name}_in"
  local out_pipe="$PIPE_DIR/${name}_out"

  mkfifo "$in_pipe" "$out_pipe" 2>/dev/null || true

  STAGE_IN_PIPES[$name]="$in_pipe"
  STAGE_OUT_PIPES[$name]="$out_pipe"

  echo "registered stage: $name"
  echo "  in:  $in_pipe"
  echo "  out: $out_pipe"
}

# connect two stages — wire one output to next input
connect_stages() {
  local from="$1" to="$2"
  # tee: data flows from→to AND gets logged
  cat "${STAGE_OUT_PIPES[$from]}" >> "${STAGE_IN_PIPES[$to]}" &
  echo "connected: $from → $to"
}

# run a stage — reads its in pipe, applies transform, writes to out pipe
run_stage() {
  local name="$1"
  local transform_file="$2"   # path to .jq file
  local in_pipe="${STAGE_IN_PIPES[$name]}"
  local out_pipe="${STAGE_OUT_PIPES[$name]}"

  log "$name" "INFO" "starting"

  while IFS= read -r record; do
    [ -z "$record" ] && continue

    metrics_inc "$name" "received"

    # apply the stage transform
    result=$(echo "$record" | jq -c \\
      --arg stage "$name" \\
      --arg ts "$(date -u +%FT%TZ)" \\
      -f "$transform_file" 2>"$LOG_DIR/${name}_errors.log")

    local exit_code=$?

    if [ $exit_code -ne 0 ] || [ -z "$result" ]; then
      # dead letter with full context
      metrics_inc "$name" "failed"
      log "$name" "ERROR" "transform failed: $(tail -1 "$LOG_DIR/${name}_errors.log")"

      echo "$record" | jq -c \\
        --arg stage "$name" \\
        --arg ts "$(date -u +%FT%TZ)" \\
        --arg err "$(tail -1 "$LOG_DIR/${name}_errors.log")" '{
          _dead_letter:    true,
          _failed_stage:   $stage,
          _failed_at:      $ts,
          _error:          $err,
          _original:       .
        }' >> "$DEAD_LETTER"
      continue
    fi

    # a transform can emit multiple records (jq outputs multiple lines)
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      echo "$line" >> "$out_pipe"
      metrics_inc "$name" "emitted"
    done <<< "$result"

  done < "$in_pipe"

  log "$name" "INFO" "finished"
}

# start a stage as a background process
start_stage() {
  local name="$1"
  local transform="$2"
  run_stage "$name" "$transform" &
  STAGE_PIDS[$name]=$!
  echo "started stage: $name (pid=${STAGE_PIDS[$name]})"
}

# graceful shutdown — drain pipes then kill
shutdown_pipeline() {
  echo ""
  echo "shutting down pipeline..."
  for name in "${!STAGE_PIDS[@]}"; do
    kill "${STAGE_PIDS[$name]}" 2>/dev/null || true
  done
  metrics_report
  echo "dead letters: $(wc -l < "$DEAD_LETTER")"
  echo "logs: $LOG_DIR"
}
trap shutdown_pipeline EXIT INT TERM
"""

        # 2. source_adapter.sh
        source_adapter_sh = """# source_adapter.sh
# every source adapter does one thing:
# call something with curl, wrap each record identically, emit to ingest pipe

emit_record() {
  local source_name="$1"
  local source_type="$2"
  local raw_json="$3"
  local out_pipe="$4"
  local seq_file="$STATE_DIR/${source_name}_seq"

  # atomic sequence increment
  local seq=$(cat "$seq_file" 2>/dev/null || echo 0)
  echo $(( seq + 1 )) > "$seq_file"

  echo "$raw_json" | jq -c \\
    --arg pid "$PIPELINE_ID" \\
    --arg name "$source_name" \\
    --arg type "$source_type" \\
    --arg ts "$(date -u +%FT%TZ)" \\
    --argjson seq "$seq" '{
      _pipeline_id:  $pid,
      _source_name:  $name,
      _source_type:  $type,
      _received_at:  $ts,
      _sequence:     $seq,
      _raw:          .
    }' >> "$out_pipe"
}

# REST polling source
source_rest_poll() {
  local name="$1"
  local out_pipe="$2"
  local interval="${3:-10}"
  local cursor_field="${4:-created_at}"
  shift 4

  local cursor_file="$STATE_DIR/${name}_cursor"
  [ ! -f "$cursor_file" ] && echo "" > "$cursor_file"

  while true; do
    local cursor=$(cat "$cursor_file")
    local url_with_cursor="${@: -1}"  # last arg is URL

    # build full request — inject cursor if we have one
    if [ -n "$cursor" ]; then
      url_with_cursor="${url_with_cursor}${url_with_cursor/*\\\\?*/&}${url_with_cursor/*\\\\?*/?}since=${cursor}"
    fi

    local all_args=("${@:1:$#-1}" "$url_with_cursor")

    response=$(curl -s \\
      -w '\\n{"__status__":%{http_code},"__time__":%{time_total}}' \\
      "${all_args[@]}" 2>>"$LOG_DIR/${name}.log" || echo -e '{\\"error\\":true}\\n{\\"__status__\\":500,\\"__time__\\":0}')

    local meta=$(echo "$response" | grep '"__status__"')
    local body=$(echo "$response" | grep -v '"__status__"')
    local status=$(echo "$meta" | jq -r '.__status__' 2>/dev/null || echo "500")

    if [ "$status" != "200" ] && [ "$status" != "201" ]; then
      log "$name" "WARN" "http=$status sleeping ${interval}s"
      sleep "$interval"
      continue
    fi

    # extract records
    local records=$(echo "$body" | jq -c '
      if type == "array" then .[]
      elif .data   | type == "array" then .data[]
      elif .items  | type == "array" then .items[]
      elif .results| type == "array" then .results[]
      elif .records| type == "array" then .records[]
      else .
      end
    ' 2>/dev/null)

    local count=0
    while IFS= read -r record; do
      [ -z "$record" ] && continue
      emit_record "$name" "rest" "$record" "$out_pipe"
      (( count++ ))
    done <<< "$records"

    log "$name" "INFO" "polled: $count records"

    # update cursor to latest value of cursor_field
    local new_cursor=$(echo "$body" | jq -r \\
      --arg f "$cursor_field" '
      [.. | objects | .[$f] // empty] | max // empty
    ' 2>/dev/null)
    [ -n "$new_cursor" ] && echo "$new_cursor" > "$cursor_file"

    sleep "$interval"
  done
}

# streaming source — SSE, chunked transfer, anything curl -N handles
source_stream() {
  local name="$1"
  local out_pipe="$2"
  shift 2

  local reconnect_delay=2

  while true; do
    log "$name" "INFO" "connecting to stream"

    curl -sN \\
      -H "Accept: text/event-stream" \\
      -H "Cache-Control: no-cache" \\
      "$@" | \\
    while IFS= read -r line; do
      if [[ "$line" =~ ^data:\\\\ (.+)$ ]]; then
        local json="${BASH_REMATCH[1]}"
        [ "$json" = "[DONE]" ] && break
        echo "$json" | jq -e . > /dev/null 2>&1 || continue
        emit_record "$name" "stream" "$json" "$out_pipe"
      elif echo "$line" | jq -e . > /dev/null 2>&1; then
        emit_record "$name" "stream" "$line" "$out_pipe"
      fi
    done

    log "$name" "WARN" "stream disconnected, reconnecting in ${reconnect_delay}s"
    sleep "$reconnect_delay"
    reconnect_delay=$(( reconnect_delay * 2 > 60 ? 60 : reconnect_delay * 2 ))
  done
}

# webhook receiver source
source_webhook() {
  local name="$1"
  local port="$2"
  local out_pipe="$3"
  local secret="${4:-}"

  log "$name" "INFO" "listening on :$port"

  while true; do
    {
      local content_length=0
      local sig_header=""
      local path=""
      local method=""

      while IFS= read -r line; do
        line="${line%$'\\\\r'}"
        [ -z "$line" ] && break
        [[ "$line" =~ ^(GET|POST|PUT|PATCH|DELETE)\\\\ ([^ ]+) ]] && \\
          method="${BASH_REMATCH[1]}" path="${BASH_REMATCH[2]}"
        [[ "$line" =~ ^Content-Length:\\\\ ([0-9]+) ]] && \\
          content_length="${BASH_REMATCH[1]}"
        [[ "$line" =~ ^X-Hub-Signature-256:\\\\ sha256=(.+) ]] && \\
          sig_header="${BASH_REMATCH[1]}"
        [[ "$line" =~ ^X-Signature-256:\\\\ (.+) ]] && \\
          sig_header="${BASH_REMATCH[1]}"
        [[ "$line" =~ ^X-Signature:\\\\ (.+) ]] && \\
          sig_header="${BASH_REMATCH[1]}"
      done

      local body=""
      if [ "$content_length" -gt 0 ]; then
        body=$(head -c "$content_length")
      fi

      local sig_valid=false
      if [ -n "$secret" ] && [ -n "$sig_header" ]; then
        local expected=$(echo -n "$body" | \\
          openssl dgst -sha256 -hmac "$secret" | awk '{print $2}')
        [ "$sig_header" = "$expected" ] && sig_valid=true
      elif [ -z "$secret" ]; then
        sig_valid=true
      fi

      if ! $sig_valid; then
        printf "HTTP/1.1 401 Unauthorized\\\\r\\\\nContent-Length: 0\\\\r\\\\n\\\\r\\\\n"
        log "$name" "WARN" "invalid signature rejected"
        continue
      fi

      if ! echo "$body" | jq -e . > /dev/null 2>&1; then
        printf "HTTP/1.1 400 Bad Request\\\\r\\\\nContent-Length: 0\\\\r\\\\n\\\\r\\\\n"
        log "$name" "WARN" "invalid JSON body rejected"
        continue
      fi

      echo "$body" | jq -c \\
        --arg path "$path" \\
        --arg method "$method" '
        . + {_http_path: $path, _http_method: $method}
      ' | while IFS= read -r enriched; do
        emit_record "$name" "webhook" "$enriched" "$out_pipe"
      done

      printf "HTTP/1.1 200 OK\\\\r\\\\nContent-Length: 2\\\\r\\\\nContent-Type: application/json\\\\r\\\\n\\\\r\\\\n{}"

    } < <(nc -l "$port" 2>/dev/null || nc -l -p "$port")
  done
}

# GraphQL source
source_graphql() {
  local name="$1"
  local url="$2"
  local out_pipe="$3"
  local query_file="$4"
  local interval="${5:-30}"
  shift 5

  while true; do
    local query=$(cat "$query_file")

    response=$(curl -s \\
      -X POST \\
      -H "Content-Type: application/json" \\
      "$@" \\
      -d "{\\"query\\": $(jq -n --arg q "$query" '$q')}" \\
      "$url")

    local errors=$(echo "$response" | jq '.errors // empty' 2>/dev/null)
    if [ -n "$errors" ]; then
      log "$name" "ERROR" "graphql errors: $errors"
    fi

    echo "$response" | jq -c '
      .data |
      if type == "object" then
        to_entries[] |
        .value |
        if type == "array" then .[]
        else .
        end
      else .
      end
    ' 2>/dev/null | while IFS= read -r record; do
      emit_record "$name" "graphql" "$record" "$out_pipe"
    done

    sleep "$interval"
  done
}
"""

        # 3. sink_adapter.sh
        sink_adapter_sh = """# sink_adapter.sh
# reads routed records, delivers to the right destination

sink_http() {
  local name="$1"
  local in_pipe="$2"
  local url="$3"
  shift 3

  log "$name" "INFO" "sink started → $url"

  while IFS= read -r record; do
    [ -z "$record" ] && continue

    code=$(echo "$record" | \\
      jq -c 'del(._pipeline_id,._source_name,._source_type,._received_at,._sequence,._stage,._valid,._validation_errors,._target,._emit_at,._raw)' | \\
      curl -s \\
        -X POST \\
        -H "Content-Type: application/json" \\
        "$@" \\
        --data-binary @- \\
        -o /dev/null \\
        -w "%{http_code}" \\
        "$url")

    if [ "$code" != "200" ] && [ "$code" != "201" ] && [ "$code" != "202" ]; then
      log "$name" "ERROR" "delivery failed: http=$code"
      echo "$record" >> "$BASE_DIR/delivery_failed.ndjson"
    else
      metrics_inc "$name" "delivered"
    fi

  done < "$in_pipe"
}

sink_file() {
  local name="$1"
  local in_pipe="$2"
  local out_file="$3"
  local rotate_lines="${4:-10000}"
  local file_num=0 line_num=0

  while IFS= read -r record; do
    [ -z "$record" ] && continue

    if (( line_num % rotate_lines == 0 )); then
      (( file_num++ ))
      current="${out_file%.ndjson}_$(printf '%04d' $file_num).ndjson"
    fi

    echo "$record" >> "$current"
    (( line_num++ ))
  done < "$in_pipe"
}

sink_router() {
  local name="$1"
  local in_pipe="$2"

  # read routed records, call correct sink based on _target
  while IFS= read -r record; do
    [ -z "$record" ] && continue

    target=$(echo "$record" | jq -r '._target // "default"')

    case "$target" in
      standard_processor)
        echo "$record" | \\
          jq -c 'del(._target,._emit_at,._pipeline_id,._stage,._valid,._validation_errors)' | \\
          curl -s -X POST \\
            -H "Authorization: Bearer ${PROCESSOR_TOKEN:-mock_token}" \\
            -H "Content-Type: application/json" \\
            --data-binary @- \\
            "${PROCESSOR_URL:-http://httpbin.org/post}" > /dev/null 2>&1 &
        ;;

      high_value_queue)
        echo "$record" | \\
          jq -c 'del(._target,._emit_at)' | \\
          curl -s -X POST \\
            -H "Authorization: Bearer ${ALERT_TOKEN:-mock_token}" \\
            -H "Content-Type: application/json" \\
            -H "X-Priority: high" \\
            --data-binary @- \\
            "${ALERT_URL:-http://httpbin.org/post}" > /dev/null 2>&1 &
        ;;

      failure_handler)
        echo "$record" | \\
          jq -c '.failure' | \\
          curl -s -X POST \\
            -H "Authorization: Bearer ${INTERNAL_TOKEN:-mock_token}" \\
            -H "Content-Type: application/json" \\
            --data-binary @- \\
            "${INTERNAL_URL:-http://httpbin.org/post}" > /dev/null 2>&1 &
        ;;

      refund_processor)
        echo "$record" | \\
          jq -c '.refund' | \\
          curl -s -X POST \\
            -H "Authorization: Bearer ${REFUND_TOKEN:-mock_token}" \\
            -H "Content-Type: application/json" \\
            --data-binary @- \\
            "${REFUND_URL:-http://httpbin.org/post}" > /dev/null 2>&1 &
        ;;

      default)
        echo "$record" >> "$BASE_DIR/unrouted.ndjson"
        ;;
    esac

    metrics_inc "sink_router" "routed_$target"

  done < "$in_pipe"
}
"""

        # 4. main.sh
        main_sh = """#!/usr/bin/env bash
# main.sh — assemble and run the pipeline

# Make sure we import relative to current scripts directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/pipeline.sh"
source "$SCRIPT_DIR/source_adapter.sh"
source "$SCRIPT_DIR/sink_adapter.sh"

echo "=== starting pipeline $PIPELINE_ID ==="

# 1. register all stages
register_stage "ingest"
register_stage "normalize"
register_stage "enrich"
register_stage "validate"
register_stage "route"

# 2. connect stages in order
connect_stages "ingest"    "normalize"
connect_stages "normalize" "enrich"
connect_stages "enrich"    "validate"
connect_stages "validate"  "route"

# 3. start stage processes
start_stage "normalize" "$STAGE_DIR/01_normalize.jq"
start_stage "enrich"    "$STAGE_DIR/02_enrich.jq"
start_stage "validate"  "$STAGE_DIR/03_validate.jq"
start_stage "route"     "$STAGE_DIR/04_route.jq"

# 4. start sink
sink_router "router" "${STAGE_OUT_PIPES[route]}" &
STAGE_PIDS[sink_router]=$!

# 5. start all sources — all write to ingest_in pipe
INGEST_PIPE="${STAGE_IN_PIPES[ingest]}"

# Mock local environment variables if not set
export PAYMENTS_TOKEN="${PAYMENTS_TOKEN:-mock_payments_token}"
export ORDERS_KEY="${ORDERS_KEY:-mock_orders_key}"
export STREAM_TOKEN="${STREAM_TOKEN:-mock_stream_token}"
export SHOPIFY_SECRET="${SHOPIFY_SECRET:-shopify_secret}"
export STRIPE_SECRET="${STRIPE_SECRET:-stripe_secret}"

# Start sources as background processes
# REST API (mock endpoints from httpbin, or users can customize)
source_rest_poll "payments_api" "$INGEST_PIPE" "15" "created_at" \\
  -H "Authorization: Bearer $PAYMENTS_TOKEN" \\
  "https://httpbin.org/anything/payments" &
STAGE_PIDS[payments_api]=$!

source_rest_poll "orders_api" "$INGEST_PIPE" "30" "updated_at" \\
  -H "X-API-Key: $ORDERS_KEY" \\
  "https://httpbin.org/anything/orders" &
STAGE_PIDS[orders_api]=$!

# webhook receivers (start local webhooks)
source_webhook "shopify_hook" "9001" "$INGEST_PIPE" "$SHOPIFY_SECRET" &
STAGE_PIDS[shopify_hook]=$!

source_webhook "stripe_hook"  "9002" "$INGEST_PIPE" "$STRIPE_SECRET" &
STAGE_PIDS[stripe_hook]=$!

echo "pipeline running. press ctrl+c to stop."
echo "logs:        $LOG_DIR"
echo "dead letter: $DEAD_LETTER"
echo ""

# live monitoring — watch metrics every 5 seconds
while true; do
  sleep 5
  printf "\\r[$(date +%T)] "
  for stage in normalize enrich validate route; do
    recv=$(cat "$STATE_DIR/${stage}_received.count"  2>/dev/null || echo 0)
    emit=$(cat "$STATE_DIR/${stage}_emitted.count"   2>/dev/null || echo 0)
    fail=$(cat "$STATE_DIR/${stage}_failed.count"    2>/dev/null || echo 0)
    printf "$stage: ↓$recv ↑$emit ✗$fail  "
  done
  dl=$(wc -l < "$DEAD_LETTER" 2>/dev/null || echo 0)
  printf "dead_letter: $dl"
done
"""

        # JQ transform contracts
        jq_normalize = """# normalize.jq
. as $envelope |
._raw as $raw |

def extract_id:
  .id // .payment_id // .paymentId // .pay_id //
  .transaction_id // .transactionId //
  .order_id // .orderId //
  ("generated_" + (now | tostring));

def extract_amount:
  (.amount // .total // .total_price // .value //
   .gross_amount // .net_amount // 0) |
  if type == "string" then
    gsub("[^0-9.]"; "") |
    if . == "" then 0
    else tonumber |
      if . < 1000 then . * 100 | round
      else round
      end
    end
  elif type == "number" then
    if . < 1000 then . * 100 | round
    else round
    end
  else 0
  end;

def extract_currency:
  (.currency // .currency_code // .currencyCode //
   .iso_currency_code // "USD") |
  ascii_upcase |
  if . == "$" or . == "USD" then "USD"
  elif . == "€" or . == "EUR" then "EUR"
  elif . == "£" or . == "GBP" then "GBP"
  else .
  end;

def extract_status:
  (.status // .state // .payment_status //
   .financial_status // .charge_status // "unknown") |
  ascii_downcase |
  if . == "succeeded" or . == "success" or
     . == "paid" or . == "complete" then "completed"
  elif . == "failed" or . == "failure" or
       . == "declined" or . == "rejected" then "failed"
  elif . == "pending" or . == "processing" or
       . == "in_progress" then "pending"
  elif . == "refunded" or . == "reversed" then "refunded"
  elif . == "cancelled" or . == "canceled" or
       . == "voided" then "cancelled"
  else .
  end;

def extract_timestamp:
  (.created_at // .createdAt // .created //
   .timestamp // .date // .processed_at //
   now) |
  if type == "number" then todate
  elif type == "string" then
    if test("^[0-9]+$") then (tonumber | todate)
    else .
    end
  else (now | todate)
  end;

def extract_customer:
  {
    id: (
      .customer_id // .customerId // .user_id //
      .userId // .buyer_id //
      .customer.id // .user.id // null |
      if . != null then tostring else null end
    ),
    email: (
      .customer_email // .email //
      .customer.email // .user.email // null
    ),
    name: (
      .customer_name //
      .customer.name //
      ((.customer.first_name // .first_name // "") + " " +
       (.customer.last_name  // .last_name  // "")) |
      if . == " " then null else ltrimstr(" ") | rtrimstr(" ") end
    )
  };

{
  _pipeline_id:  $envelope._pipeline_id,
  _source_name:  $envelope._source_name,
  _source_type:  $envelope._source_type,
  _received_at:  $envelope._received_at,
  _sequence:     $envelope._sequence,
  _stage:        "normalized",
  id:            ($raw | extract_id),
  amount_cents:  ($raw | extract_amount),
  currency:      ($raw | extract_currency),
  status:        ($raw | extract_status),
  event_type:    ($raw.type // $raw.event // $raw.event_type // "payment"),
  created_at:    ($raw | extract_timestamp),
  customer:      ($raw | extract_customer),
  metadata: (
    $raw.metadata // $raw.meta // $raw.custom_data // {}
  ),
  _raw: $raw
}
"""

        jq_enrich = """# enrich.jq
. as $rec |

def amount_usd:
  if .currency == "USD" then .amount_cents / 100
  else .amount_cents / 100
  end;

def amount_class:
  .amount_cents |
  if . == 0              then "zero"
  elif . < 100           then "micro"
  elif . < 1000          then "small"
  elif . < 10000         then "medium"
  elif . < 100000        then "large"
  else "enterprise"
  end;

def time_of_day:
  .created_at | fromdateiso8601 |
  (. % 86400) as $sod |
  if $sod < 21600   then "night"
  elif $sod < 43200 then "morning"
  elif $sod < 64800 then "afternoon"
  else "evening"
  end;

def day_of_week:
  .created_at | fromdateiso8601 |
  ((. / 86400 | floor) + 4) % 7 |
  ["sun","mon","tue","wed","thu","fri","sat"][.];

def is_retry:
  .metadata.retry_count != null and
  (.metadata.retry_count | tonumber) > 0;

def processing_age_seconds:
  (now - (.created_at | fromdateiso8601)) | floor;

$rec + {
  _stage: "enriched",
  amount_usd:          ($rec | amount_usd),
  amount_class:        ($rec | amount_class),
  time_of_day:         ($rec | time_of_day),
  day_of_week:         ($rec | day_of_week),
  is_retry:            ($rec | is_retry),
  processing_age_sec:  ($rec | processing_age_seconds),
  risk_signals: [
    if .amount_cents > 100000         then "high_value"       else empty end,
    if (.customer.id == null)         then "anonymous"        else empty end,
    if ($rec | is_retry)              then "retry"            else empty end,
    if .status == "failed" and
       .amount_cents > 10000          then "high_value_fail"  else empty end,
    if (.metadata.first_transaction
        // false)                     then "first_time"       else empty end
  ],
  route_to: (
    if .status == "failed"            then "failure_handler"
    elif .amount_cents > 100000       then "high_value_queue"
    elif .status == "refunded"        then "refund_processor"
    else                                   "standard_processor"
    end
  )
}
"""

        jq_validate = """# validate.jq
. as $rec |

def check(cond; msg):
  if cond then empty else msg end;

[
  check(.id != null;                          "missing id"),
  check(.id | type == "string";               "id must be string"),
  check(.amount_cents | type == "number";     "amount_cents must be number"),
  check(.amount_cents >= 0;                   "amount_cents must be non-negative"),
  check(.currency | test("^[A-Z]{3}$");       "currency must be 3-char ISO code"),
  check(.status | IN(
    "completed","failed","pending",
    "refunded","cancelled","unknown"
  );                                          "unrecognized status"),
  check(.created_at | test("^\\\\d{4}-");       "created_at must be ISO8601"),
  check(.customer | type == "object";         "customer must be object"),
  check(.event_type | type == "string";       "event_type required")
] as $errors |

if ($errors | length) == 0 then
  $rec + {_valid: true, _validation_errors: []}
else
  $rec + {_valid: false, _validation_errors: $errors}
end
"""

        jq_route = """# route.jq
. as $rec |

select(._valid == true) |

if .route_to == "standard_processor" then
  {
    _target:        "standard_processor",
    _emit_at:       (now | todate),
    payment_id:     .id,
    amount:         (.amount_cents / 100),
    currency:       .currency,
    status:         .status,
    customer_id:    .customer.id,
    customer_email: .customer.email,
    event:          .event_type,
    metadata:       .metadata,
    amount_class:   .amount_class,
    risk_signals:   .risk_signals,
    source:         ._source_name
  }

elif .route_to == "high_value_queue" then
  {
    _target:          "high_value_queue",
    _priority:        "high",
    _emit_at:         (now | todate),
    transaction: {
      id:           .id,
      amount_cents: .amount_cents,
      amount_usd:   .amount_usd,
      currency:     .currency,
      status:       .status,
      created_at:   .created_at,
      age_seconds:  .processing_age_sec
    },
    customer:         .customer,
    risk: {
      signals:      .risk_signals,
      requires_review: (.risk_signals | length > 0)
    },
    source:           ._source_name,
    raw:              ._raw
  }

elif .route_to == "failure_handler" then
  {
    _target:       "failure_handler",
    _emit_at:      (now | todate),
    failure: {
      payment_id:  .id,
      amount_cents:.amount_cents,
      currency:    .currency,
      customer_id: .customer.id,
      event_type:  .event_type,
      failed_at:   .created_at,
      is_retry:    .is_retry,
      retry_count: (.metadata.retry_count // 0 | tonumber),
      retryable:   (
        .event_type | IN(
          "payment.failed",
          "charge.failed"
        )
      )
    },
    source:        ._source_name
  }

elif .route_to == "refund_processor" then
  {
    _target:       "refund_processor",
    _emit_at:      (now | todate),
    refund: {
      original_payment_id: (
        .metadata.original_payment_id //
        .metadata.payment_id //
        .id
      ),
      refund_amount_cents: .amount_cents,
      currency:            .currency,
      reason:              (.metadata.refund_reason // "not_provided"),
      customer_id:         .customer.id,
      initiated_at:        .created_at
    },
    source:        ._source_name
  }

else
  . + {_target: "default"}
end
"""

        # Write all files
        def write_file(filename: str, content: str) -> None:
            path = os.path.join(self.base_dir, filename)
            with open(path, "w") as f:
                f.write(content)
            os.chmod(path, 0o755)

        write_file("pipeline.sh", pipeline_sh)
        write_file("source_adapter.sh", source_adapter_sh)
        write_file("sink_adapter.sh", sink_adapter_sh)
        write_file("main.sh", main_sh)

        # Write JQ files
        with open(os.path.join(stages_dir, "01_normalize.jq"), "w") as f:
            f.write(jq_normalize)
        with open(os.path.join(stages_dir, "02_enrich.jq"), "w") as f:
            f.write(jq_enrich)
        with open(os.path.join(stages_dir, "03_validate.jq"), "w") as f:
            f.write(jq_validate)
        with open(os.path.join(stages_dir, "04_route.jq"), "w") as f:
            f.write(jq_route)

        # Write run_5_curls.sh
        run_5_curls_content = """#!/usr/bin/env bash
# run_5_curls.sh — Feed 5 distinct API formats into the pylow live pipeline
set -euo pipefail

if [ ! -f /tmp/pylow_pipeline_latest ]; then
  echo "Error: No active pipeline found. Please run 'pylow pipeline-run' first in another window."
  exit 1
fi

ACTIVE_DIR=$(cat /tmp/pylow_pipeline_latest)
INGEST_PIPE="$ACTIVE_DIR/pipes/ingest_in"

echo "=========================================================="
echo " Starting 5 Curl Sources feeding into $INGEST_PIPE"
echo "=========================================================="

# 1. Shopify Webhook mock
echo "🚀 Source 1: Sending Shopify webhook event..."
curl -s -X POST \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": "shop_505", "total_price": "89.99", "currencyCode": "USD", "financial_status": "paid"}' \\
  http://localhost:9001 >/dev/null || true

# 2. Stripe Webhook mock
echo "🚀 Source 2: Sending Stripe webhook event (High Value)..."
curl -s -X POST \\
  -H "Content-Type: application/json" \\
  -d '{"id": "ch_stripe_999", "amount": 150000, "currency": "usd", "status": "succeeded"}' \\
  http://localhost:9002 >/dev/null || true

# 3. Legacy API transaction mock
echo "🚀 Source 3: Polling Legacy API (Returns different shape)..."
curl -s "https://httpbin.org/anything" \\
  | jq -c --arg id "legacy_$(date +%s)" '{
    "pay_id": $id,
    "value": "45.00",
    "currency_code": "EUR",
    "state": "complete"
  }' >> "$INGEST_PIPE"

# 4. Failed Refund Event mock
echo "🚀 Source 4: Simulating failed refund event..."
curl -s "https://httpbin.org/anything" \\
  | jq -c --arg id "ref_$(date +%s)" '{
    "transaction_id": $id,
    "amount": 12000,
    "currency": "USD",
    "status": "refunded",
    "metadata": {
      "refund_reason": "customer_request"
    }
  }' >> "$INGEST_PIPE"

# 5. Invalid/Malformed Payload mock
echo "🚀 Source 5: Sending malformed payload (Missing currency)..."
curl -s "https://httpbin.org/anything" \\
  | jq -c --arg id "bad_$(date +%s)" '{
    "id": $id,
    "amount": "not-a-number",
    "currency": "INVALID_CURR",
    "status": "unknown"
  }' >> "$INGEST_PIPE"

echo "=========================================================="
echo " All 5 sources sent to pipeline!"
echo "=========================================================="
"""
        write_file("run_5_curls.sh", run_5_curls_content)

    def run(self) -> None:
        self._prepare_scripts()
        print(_c("BOLD", "=== Starting Live Source-Agnostic Transformation Pipeline ==="))
        main_script = os.path.join(self.base_dir, "main.sh")
        try:
            # Execute main.sh in the foreground to let users view progress
            subprocess.run([main_script], check=True)
        except KeyboardInterrupt:
            print(_c("YELLOW", "\nPipeline stopped by user (Ctrl+C)."))
        except subprocess.CalledProcessError as e:
            print(_c("RED", f"Pipeline encountered error: {e}"))

    def _get_active_pipeline_dir(self) -> str:
        latest_file = "/tmp/pylow_pipeline_latest"
        if not os.path.exists(latest_file):
            print(_c("RED", "No active pipeline directory found. Run the pipeline first."))
            sys.exit(1)
        with open(latest_file) as f:
            return f.read().strip()

    def inject(self, record_raw: str, stage: str = "ingest") -> None:
        try:
            # Try to validate JSON first
            json.loads(record_raw)
        except Exception as e:
            print(_c("RED", f"Invalid JSON record: {e}"))
            return

        pipeline_dir = self._get_active_pipeline_dir()
        pipe_path = os.path.join(pipeline_dir, "pipes", f"{stage}_in")

        if not os.path.exists(pipe_path):
            print(_c("RED", f"Target stage pipe '{pipe_path}' does not exist."))
            return

        # Prepare injection command (running jq to add envelope properties)
        inject_cmd = (
            f"echo '{record_raw}' | jq -c "
            f"--arg pid 'manual' "
            f"--arg ts '$(date -u +%FT%TZ)' "
            f"'. + {{ _pipeline_id: $pid, _source_name: \"manual_inject\", "
            f"_source_type: \"test\", _received_at: $ts, _sequence: -1, _raw: . }}' "
            f">> {pipe_path}"
        )
        try:
            subprocess.run(inject_cmd, shell=True, check=True)
            print(_c("GREEN", f"✓ Injected record to stage '{stage}' in active pipeline."))
        except Exception as e:
            print(_c("RED", f"Failed to inject record: {e}"))

    def replay(self, filter_jq: str = ".", target_stage: str = "normalize") -> None:
        pipeline_dir = self._get_active_pipeline_dir()
        dead_letter_path = os.path.join(pipeline_dir, "dead_letter.ndjson")
        pipe_path = os.path.join(pipeline_dir, "pipes", f"{target_stage}_in")

        if not os.path.exists(dead_letter_path) or os.path.getsize(dead_letter_path) == 0:
            print(_c("YELLOW", "Dead letter box is empty. Nothing to replay."))
            return

        if not os.path.exists(pipe_path):
            print(_c("RED", f"Target pipe '{pipe_path}' does not exist."))
            return

        replay_cmd = (
            f"while IFS= read -r record; do "
            f"  [ -z \"$record\" ] && continue; "
            f"  echo \"$record\" | jq -c --arg ts \"$(date -u +%FT%TZ)\" "
            f"    'select(._dead_letter == true) | ._original + "
            f"     {{ _replayed: true, _replayed_at: $ts, _replay_from: ._failed_stage }}' "
            f"    >> {pipe_path}; "
            f"done < <(jq -c '{filter_jq}' {dead_letter_path})"
        )
        try:
            subprocess.run(replay_cmd, shell=True, check=True, executable="/bin/bash")
            print(_c("GREEN", f"✓ Replayed records matching '{filter_jq}' into stage '{target_stage}'."))
        except Exception as e:
            print(_c("RED", f"Failed to replay records: {e}"))

    def test_stage(self, record_raw: str, transform_file: str) -> None:
        self._prepare_scripts()
        # Find local jq transform file
        local_jq = os.path.join(self.base_dir, "stages", transform_file)
        if not os.path.exists(local_jq):
            # Try stages path
            local_jq = os.path.join(self.base_dir, transform_file)
            if not os.path.exists(local_jq):
                print(_c("RED", f"Transform file '{transform_file}' not found."))
                return

        print(_c("BOLD", f"=== Testing Transform: {transform_file} ==="))
        print("Input:")
        try:
            parsed = json.loads(record_raw)
            print(json.dumps(parsed, indent=2))
        except Exception:
            print(record_raw)

        print("\nOutput:")
        try:
            # Add basic envelope mock elements for normalize test
            if "normalize" in transform_file:
                envelope = {
                    "_pipeline_id": "test_run",
                    "_source_name": "test_source",
                    "_source_type": "test_type",
                    "_received_at": "2026-06-11T12:00:00Z",
                    "_sequence": 1,
                    "_raw": json.loads(record_raw)
                }
                record_to_run = json.dumps(envelope)
            else:
                record_to_run = record_raw

            p = subprocess.Popen(["jq", "-c", "-f", local_jq], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = p.communicate(input=record_to_run)
            if p.returncode == 0:
                for line in out.splitlines():
                    if line.strip():
                        print(json.dumps(json.loads(line), indent=2))
            else:
                print(_c("RED", f"Error in jq execution: {err}"))
        except Exception as e:
            print(_c("RED", f"Failed to test transform: {e}"))

    def tap(self, stage: str) -> None:
        pipeline_dir = self._get_active_pipeline_dir()
        log_path = os.path.join(pipeline_dir, "logs", f"{stage}.log")

        if not os.path.exists(log_path):
            print(_c("RED", f"Log file for stage '{stage}' does not exist at {log_path}"))
            return

        print(_c("BOLD", f"=== Tapping Stage logs: {stage} ==="))
        try:
            # Tail the log
            subprocess.run(["tail", "-n", "20", log_path])
        except KeyboardInterrupt:
            pass
