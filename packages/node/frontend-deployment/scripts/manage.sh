#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PKG_DIR/docker-compose.yml"

PORTS=(31410 31411 31412 31413 31414 31415 31416 31417 31418)

get_docker_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

free_port() {
  local port=$1
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -i:"${port}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo -e "${YELLOW}  - Terminating process(es) on port ${port}: ${pids}${NC}"
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

cmd_free_ports() {
  echo -e "${BLUE}[frontend-deployment] Freeing all stack ports (31410-31418)...${NC}"
  for p in "${PORTS[@]}"; do
    free_port "$p"
  done
  echo -e "${GREEN}✓ All stack ports verified/freed.${NC}"
}

cmd_up() {
  local bin
  bin=$(get_docker_compose_cmd)
  if [ -z "$bin" ]; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
  fi
  echo -e "${BLUE}[frontend-deployment] Starting unified infrastructure stack...${NC}"
  $bin -f "$COMPOSE_FILE" up -d
  echo -e "${GREEN}✓ All infrastructure services started successfully!${NC}"
  echo -e "${BOLD}Service Endpoints:${NC}"
  echo -e "  - Traefik Gateway: http://localhost:31410"
  echo -e "  - Traefik Dashboard: http://localhost:31411"
  echo -e "  - AlloyDB/PostgreSQL: localhost:31412"
  echo -e "  - Redis: localhost:31413"
  echo -e "  - Kafka: localhost:31414"
  echo -e "  - Grafana UI: http://localhost:31415 (admin / admin)"
  echo -e "  - Grafana Tempo: http://localhost:31416"
  echo -e "  - OTel Collector HTTP: http://localhost:31417"
  echo -e "  - OTel Collector gRPC: localhost:31418"
}

cmd_down() {
  local bin
  bin=$(get_docker_compose_cmd)
  if [ -z "$bin" ]; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
  fi
  echo -e "${BLUE}[frontend-deployment] Stopping infrastructure stack...${NC}"
  $bin -f "$COMPOSE_FILE" down
  echo -e "${GREEN}✓ All services stopped.${NC}"
}

cmd_status() {
  local bin
  bin=$(get_docker_compose_cmd)
  if [ -z "$bin" ]; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
  fi
  $bin -f "$COMPOSE_FILE" ps
}

cmd_logs() {
  local bin
  bin=$(get_docker_compose_cmd)
  if [ -z "$bin" ]; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
  fi
  $bin -f "$COMPOSE_FILE" logs -f "$@"
}

COMMAND=${1:-"help"}
shift || true

case "$COMMAND" in
  up)
    cmd_up
    ;;
  down)
    cmd_down
    ;;
  status)
    cmd_status
    ;;
  logs)
    cmd_logs "$@"
    ;;
  free-ports)
    cmd_free_ports
    ;;
  *)
    echo "Usage: $0 {up|down|status|logs|free-ports}"
    exit 1
    ;;
esac
