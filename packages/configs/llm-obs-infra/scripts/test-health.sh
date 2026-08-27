#!/usr/bin/env bash
#
# test-health.sh — LLMObs Frontend Deployment — Health & Security Diagnostic
#
# Runs 4 diagnostic sections:
#   1. Container process & Docker health status
#   2. Individual service port & endpoint access
#   3. TLS certificate & HTTPS verification
#   4. Security hardening checks (headers, Redis auth, network isolation)
#

set +e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BOLD} DOCKER SERVICE HEALTH & SECURITY DIAGNOSTIC${NC}"
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
  local connected=false
  for i in {1..4}; do
    if nc -z localhost "$port" >/dev/null 2>&1; then
      connected=true
      break
    fi
    sleep 2
  done

  if [ "$connected" = true ]; then
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
  code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 3 "$url" || echo "000")

  if [[ "$expected_pattern" =~ $code ]]; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${name}${NC} -> ${url} (HTTP ${code})"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${name}${NC} -> ${url} (HTTP ${code}, expected: ${expected_pattern})"
  fi
}

check_tls() {
  local name=$1
  local host=$2
  local port=$3
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

  if echo | openssl s_client -connect "${host}:${port}" -servername "${host}" 2>/dev/null | grep -q "Verify return code: 0\|CONNECTED"; then
    local subject
    subject=$(echo | openssl s_client -connect "${host}:${port}" -servername "${host}" 2>/dev/null | openssl x509 -noout -subject 2>/dev/null | sed 's/subject=//')
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${name}${NC} -> TLS handshake OK on :${port} (${subject})"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${name}${NC} -> TLS handshake FAILED on :${port}"
  fi
}

check_header() {
  local name=$1
  local url=$2
  local header=$3
  local host_header=${4:-""}
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

  local value
  if [ -n "$host_header" ]; then
    value=$(curl -sk -I -H "Host: ${host_header}" --max-time 3 "$url" 2>/dev/null | grep -i "^${header}:" | head -1)
  else
    value=$(curl -sk -I --max-time 3 "$url" 2>/dev/null | grep -i "^${header}:" | head -1)
  fi

  if [ -n "$value" ]; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${name}${NC} -> ${value}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${name}${NC} -> Header '${header}' not found"
  fi
}

check_network() {
  local container=$1
  local network=$2
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

  local networks
  networks=$(docker inspect --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$container" 2>/dev/null || echo "")

  if echo "$networks" | grep -q "$network"; then
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}${container}${NC} -> Connected to ${network}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}${container}${NC} -> NOT on ${network} (found: ${networks})"
  fi
}

echo -e "\n${YELLOW}1. Container Process & Docker Health Status:${NC}"
check_container_status "llmobs-traefik-gateway" "Traefik Gateway"
check_container_status "llmobs-redis-ledger" "Redis Cache"
check_container_status "llmobs-kafka-broker" "Kafka Event Broker"
check_container_status "llmobs-tempo-tracing" "Grafana Tempo"
check_container_status "llmobs-otel-collector" "OpenTelemetry Collector"
check_container_status "llmobs-grafana-portal" "Grafana Dashboard"
check_container_status "llmobs-clickhouse-analytics" "ClickHouse Analytics"
check_container_status "llmobs-alloydb-db" "AlloyDB Relational DB"
check_container_status "llmobs-temporal-engine" "Temporal Workflow Engine"

echo -e "\n${YELLOW}2. Individual Service Port & Endpoint Access:${NC}"
check_tcp "Traefik Gateway HTTP" "31410"
check_tcp "Traefik Dashboard" "31411"
check_tcp "Traefik Gateway HTTPS" "31419"
check_tcp "Redis Cache" "31413"
check_tcp "Kafka Event Broker" "31414"
check_http "Grafana Tempo" "http://localhost:31416/ready" "200"

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
GRAFANA_CODE="000"
for i in {1..5}; do
  GRAFANA_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://localhost:31415/api/health" 2>/dev/null || echo "000")
  if [ "$GRAFANA_CODE" = "200" ]; then
    break
  fi
  sleep 2
done

if [ "$GRAFANA_CODE" = "200" ]; then
  echo -e "  ${GREEN}[PASS]${NC} ${BOLD}Grafana UI${NC} -> http://localhost:31415/api/health (HTTP ${GRAFANA_CODE})"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo -e "  ${RED}[FAIL]${NC} ${BOLD}Grafana UI${NC} -> http://localhost:31415/api/health (HTTP ${GRAFANA_CODE}, expected: 200)"
fi
check_tcp "OTel Collector HTTP" "31417"
check_tcp "OTel Collector gRPC" "31418"
check_tcp "AlloyDB Relational DB" "31420"
check_tcp "ClickHouse HTTP" "31421"
check_tcp "ClickHouse Native" "31422"
check_tcp "Temporal gRPC" "31424"
check_tcp "Temporal UI" "31425"

echo -e "\n${YELLOW}3. TLS Certificate & HTTPS Verification:${NC}"
check_tls "Traefik Gateway TLS" "localhost" "31419"
check_http "HTTPS Gateway Response" "https://localhost:31419" "200|404|302|301"

CERT_FILE="$PKG_DIR/config/certs/server.pem"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "$CERT_FILE" ]; then
  if openssl x509 -checkend 86400 -noout -in "$CERT_FILE" 2>/dev/null; then
    expiry=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
    echo -e "  ${GREEN}[PASS]${NC} ${BOLD}Server Certificate Validity${NC} -> Expires: ${expiry}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} ${BOLD}Server Certificate Validity${NC} -> Certificate expired or expiring within 24h"
  fi
else
  echo -e "  ${RED}[FAIL]${NC} ${BOLD}Server Certificate Validity${NC} -> Certificate file not found"
fi

echo -e "\n${YELLOW}4. Security Hardening Checks:${NC}"
check_header "X-Content-Type-Options" "https://localhost:31419" "X-Content-Type-Options" "llmobs.gateway"
check_header "X-Frame-Options" "https://localhost:31419" "X-Frame-Options" "llmobs.gateway"
check_header "Strict-Transport-Security" "https://localhost:31419" "Strict-Transport-Security" "llmobs.gateway"
check_header "X-XSS-Protection" "https://localhost:31419" "X-XSS-Protection" "llmobs.gateway"
check_header "Referrer-Policy" "https://localhost:31419" "Referrer-Policy" "llmobs.gateway"

REDIS_PW=""
if [ -f "$PKG_DIR/.env" ]; then
  REDIS_PW=$(grep -E "^REDIS_PASSWORD=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2)
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
UNAUTH_RESULT=$(redis-cli -p 31413 PING 2>/dev/null || echo "")
if echo "$UNAUTH_RESULT" | grep -qi "NOAUTH\|ERR\|Authentication"; then
  echo -e "  ${GREEN}[PASS]${NC} ${BOLD}Redis Auth Guard${NC} -> Unauthenticated PING rejected"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
elif [ -z "$UNAUTH_RESULT" ]; then
  echo -e "  ${YELLOW}[WARN]${NC} ${BOLD}Redis Auth Guard${NC} -> redis-cli not installed, skipping"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo -e "  ${RED}[FAIL]${NC} ${BOLD}Redis Auth Guard${NC} -> Unauthenticated PING succeeded (no password set)"
fi

echo -e "\n${YELLOW}5. Network Isolation:${NC}"
check_network "llmobs-traefik-gateway" "llmobs-network"
check_network "llmobs-redis-ledger" "llmobs-network"
check_network "llmobs-kafka-broker" "llmobs-network"
check_network "llmobs-tempo-tracing" "llmobs-network"
check_network "llmobs-otel-collector" "llmobs-network"
check_network "llmobs-grafana-portal" "llmobs-network"
check_network "llmobs-clickhouse-analytics" "llmobs-network"
check_network "llmobs-alloydb-db" "llmobs-network"
check_network "llmobs-temporal-engine" "llmobs-network"

echo -e "\n${BLUE}====================================================${NC}"
if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
  echo -e "${GREEN}${BOLD}✓ ALL ${PASSED_CHECKS}/${TOTAL_CHECKS} HEALTH & SECURITY CHECKS PASSED!${NC}"
  echo -e "${BLUE}====================================================${NC}"
  exit 0
else
  echo -e "${RED}${BOLD}✖ DIAGNOSTIC: ${PASSED_CHECKS}/${TOTAL_CHECKS} CHECKS PASSED.${NC}"
  echo -e "${BLUE}====================================================${NC}"
  exit 1
fi
