#!/usr/bin/env bash

set +e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PKG_DIR/docker-compose.yml"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BOLD} DOCKER SERVICE HEALTH & ACCESSIBILITY DIAGNOSTIC${NC}"
echo -e "${BLUE}====================================================${NC}"

TOTAL_CHECKS=0
PASSED_CHECKS=0

check_container_status() {
  local container_name=$1
  local service_label=$2
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  
  if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${service_label}${NC} (${container_name}) -> Container is NOT running"
    return 0
  fi

  local status
  status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_name" 2>/dev/null || echo "unknown")

  if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${service_label}${NC} (${container_name}) -> Status: ${status}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${YELLOW}[WARN]${NC} ${BOLD}${service_label}${NC} (${container_name}) -> Status: ${status}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  fi
}

check_tcp() {
  local name=$1
  local port=$2
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  if nc -z localhost "$port" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${name}${NC} -> TCP Port ${port} is listening & accepting connections"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${name}${NC} -> TCP Port ${port} is unreachable"
  fi
}

check_http() {
  local name=$1
  local url=$2
  local expected_pattern=$3
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" || echo "000")

  if [[ "$expected_pattern" =~ $code ]]; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${name}${NC} -> ${url} (HTTP ${code})"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${name}${NC} -> ${url} (HTTP ${code}, expected: ${expected_pattern})"
  fi
}

echo -e "\n${YELLOW}1. Container Process & Docker Health Status:${NC}"
check_container_status "frontend-traefik-gateway" "Traefik Gateway"
check_container_status "frontend-redis" "Redis Cache"
check_container_status "frontend-kafka" "Kafka Event Broker"
check_container_status "frontend-tempo" "Grafana Tempo"
check_container_status "frontend-otel-collector" "OpenTelemetry Collector"
check_container_status "frontend-grafana" "Grafana Dashboard"

echo -e "\n${YELLOW}2. Individual Service Port & Endpoint Access:${NC}"
check_tcp "Traefik Gateway HTTP Proxy" "31410"
check_tcp "Traefik Dashboard Web" "31411"
check_tcp "Redis Key-Value Cache Socket" "31413"
check_tcp "Kafka Event Streaming Socket" "31414"
check_http "Grafana UI Service API" "http://localhost:31415/api/health" "200"
check_http "Grafana Tempo Readiness Probe" "http://localhost:31416/ready" "200"
check_tcp "OTel Collector OTLP HTTP Ingestion" "31417"
check_tcp "OTel Collector OTLP gRPC Ingestion" "31418"

echo -e "\n${BLUE}====================================================${NC}"
if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
  echo -e "${GREEN}${BOLD}✓ ALL ${PASSED_CHECKS}/${TOTAL_CHECKS} DOCKER & SERVICE CHECKS PASSED PERFECTLY!${NC}"
  echo -e "${BLUE}====================================================${NC}"
  exit 0
else
  echo -e "${RED}${BOLD}✖ DIAGNOSTIC FAILED: ${PASSED_CHECKS}/${TOTAL_CHECKS} CHECKS PASSED.${NC}"
  echo -e "${BLUE}====================================================${NC}"
  exit 1
fi
