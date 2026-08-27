#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

print_service_endpoints() {
  echo -e "${GREEN}✓ All infrastructure services started/restarted successfully!${NC}"
  echo -e "${BOLD}Service Endpoints:${NC}"
  echo -e "  - Traefik Gateway HTTP:  http://localhost:31410  (→ redirects to HTTPS)"
  echo -e "  - Traefik Gateway HTTPS: https://localhost:31419"
  echo -e "  - Traefik Dashboard:     http://localhost:31411"
  echo -e "  - Redis (auth required): localhost:31413"
  echo -e "  - Kafka:                 localhost:31414"
  echo -e "  - Grafana UI:            https://llmobs.grafana:31419"
  echo -e "  - Grafana Tempo:         https://llmobs.tempo:31419"
  echo -e "  - OTel Collector HTTP:   http://localhost:31417"
  echo -e "  - OTel Collector gRPC:   localhost:31418"
}

wait_with_exponential_backoff_jitter() {
  local check_cmd=$1
  local max_attempts=${2:-6}
  local base_delay=${3:-1}
  local max_delay=${4:-12}
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    if eval "$check_cmd" >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
      break
    fi

    local exp=$((1 << attempt))
    local cap=$((base_delay * exp))
    if [ $cap -gt $max_delay ]; then
      cap=$max_delay
    fi

    local jitter=$(( (RANDOM % cap) + 1 ))
    sleep "$jitter"
  done
  return 1
}

wait_for_container_health() {
  local container=$1
  echo -e "${BLUE}  - Waiting for container ${container} to complete startup...${NC}"
  local check_cmd="docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' '$container' 2>/dev/null | grep -q 'healthy\|running'"
  if wait_with_exponential_backoff_jitter "$check_cmd" 6 1 8; then
    echo -e "${GREEN}✓ ${container} is ready.${NC}"
    return 0
  fi
  echo -e "${YELLOW}⚠️ ${container} initialization still in progress...${NC}"
}

wait_for_clickhouse_http() {
  echo -e "${BLUE}  - Waiting for ClickHouse HTTP & Native TCP socket binding...${NC}"
  local check_cmd="curl -s http://localhost:31421/ping 2>/dev/null | grep -q 'Ok.'"
  if wait_with_exponential_backoff_jitter "$check_cmd" 7 1 12; then
    echo -e "${GREEN}✓ ClickHouse HTTP (31421) & Native (31422) endpoints ready.${NC}"
    return 0
  fi
  echo -e "${YELLOW}⚠️ ClickHouse socket binding taking longer than expected...${NC}"
}

wait_for_web_gateways() {
  echo -e "${BLUE}  - Waiting for Grafana UI & Temporal engine socket bindings...${NC}"
  local check_cmd="curl -s http://localhost:31415/api/health 2>/dev/null | grep -q 'ok' && nc -z localhost 31424 2>/dev/null"
  if wait_with_exponential_backoff_jitter "$check_cmd" 7 1 12; then
    echo -e "${GREEN}✓ Grafana UI (31415) & Temporal gRPC (31424) endpoints ready.${NC}"
    return 0
  fi
  echo -e "${YELLOW}⚠️ Gateway initialization still in progress...${NC}"
}

wait_for_alloydb() {
  echo -e "${BLUE}  - Waiting for AlloyDB database engine consistent recovery state...${NC}"
  local check_cmd="docker exec -i llmobs-alloydb-db pg_isready -U admin -d llm_observability"
  if wait_with_exponential_backoff_jitter "$check_cmd" 8 1 12; then
    echo -e "${GREEN}✓ AlloyDB relational database ready.${NC}"
    return 0
  fi
  echo -e "${YELLOW}⚠️ AlloyDB database recovery taking longer than expected...${NC}"
}

ensure_external_network() {
  local net_name="llmobs-network"
  if ! docker network inspect "$net_name" >/dev/null 2>&1; then
    echo -e "${BLUE}⚡ Creating external Docker network '${net_name}' with platform network signature...${NC}"
    docker network create \
      --driver bridge \
      --subnet 172.28.0.0/16 \
      --gateway 172.28.0.1 \
      --label "com.llmobs.network.signature=llmobs-net-sig-v1.0" \
      --label "com.llmobs.network.security=isolated-bridge" \
      --label "com.llmobs.network.managed-by=llmobs-infra" \
      "$net_name" >/dev/null 2>&1 || true
  fi
}

start_ordered_stack() {
  local bin=$1
  local compose_file=$2

  ensure_external_network

  echo -e "${BLUE}⚡ Step 1/3: Starting core databases (AlloyDB, Redis, ClickHouse)...${NC}"
  $bin -f "$compose_file" up -d llmobs-alloydb llmobs-redis llmobs-clickhouse || true
  wait_for_alloydb
  wait_for_clickhouse_http 20

  echo -e "${BLUE}⚡ Step 2/3: Starting telemetry & event streams (Kafka, Tempo, OTel Collector)...${NC}"
  $bin -f "$compose_file" up -d llmobs-kafka llmobs-tempo llmobs-otel-collector || true

  echo -e "${BLUE}⚡ Step 3/3: Starting web gateways & orchestration engines (Traefik, Grafana, Temporal)...${NC}"
  $bin -f "$compose_file" up -d llmobs-traefik llmobs-grafana llmobs-temporal || true
  wait_for_web_gateways 20

  print_service_endpoints
}

main() {
  local bin=$1
  local compose_file=$2
  start_ordered_stack "$bin" "$compose_file"
}

main "$@"
