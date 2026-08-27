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

wait_for_container_health() {
  local container=$1
  local max_wait_sec=${2:-30}
  local elapsed=0

  echo -e "${BLUE}  - Waiting for container ${container} to complete startup...${NC}"
  while [ $elapsed -lt $max_wait_sec ]; do
    local status
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
      echo -e "${GREEN}✓ ${container} is ready (${status}).${NC}"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo -e "${YELLOW}⚠️ ${container} initialization still in progress...${NC}"
}

start_ordered_stack() {
  local bin=$1
  local compose_file=$2

  echo -e "${BLUE}⚡ Step 1/3: Starting core databases (AlloyDB, Redis, ClickHouse)...${NC}"
  $bin -f "$compose_file" up -d llmobs-alloydb llmobs-redis llmobs-clickhouse
  wait_for_container_health "llmobs-clickhouse-analytics" 15
  wait_for_container_health "llmobs-alloydb-db" 15

  echo -e "${BLUE}⚡ Step 2/3: Starting telemetry & event streams (Kafka, Tempo, OTel Collector)...${NC}"
  $bin -f "$compose_file" up -d llmobs-kafka llmobs-tempo llmobs-otel-collector

  echo -e "${BLUE}⚡ Step 3/3: Starting web gateways & orchestration engines (Traefik, Grafana, Temporal)...${NC}"
  $bin -f "$compose_file" up -d --force-recreate

  print_service_endpoints
}

main() {
  local bin=$1
  local compose_file=$2
  start_ordered_stack "$bin" "$compose_file"
}

main "$@"
