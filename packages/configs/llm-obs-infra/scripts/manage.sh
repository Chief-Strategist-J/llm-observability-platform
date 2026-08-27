#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

CURRENT_SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$CURRENT_SCRIPT_DIR/discovery/dynamic-discovery.sh"

get_stack_ports() {
  echo "31410 31411 31412 31413 31414 31415 31416 31417 31418 31419 31420 31421 31422 31423 31424 31425"
}

get_docker_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

find_required_script() {
  local script_name=$1
  local search_root=$2
  local found
  found=$(discover_script_file_recursive "$script_name" "$search_root" || echo "")

  if [ -z "$found" ]; then
    echo -e "${RED}Error: Required script '$script_name' not found dynamically under '$search_root'.${NC}" >&2
    exit 1
  fi
  echo "$found"
}

ensure_env_file() {
  local pkg_dir=$1
  if [ ! -f "$pkg_dir/.env" ] && [ -f "$pkg_dir/.env.example" ]; then
    echo -e "${BLUE}⚡ Generating default .env file from .env.example...${NC}"
    cp "$pkg_dir/.env.example" "$pkg_dir/.env"
  fi
}

execute_up_pipeline() {
  local bin=$1
  local compose_file=$2
  local scripts_root=$3
  local ports=$4
  local pkg_dir=$5

  ensure_env_file "$pkg_dir"

  local prereq_script
  prereq_script=$(find_required_script "system-prereqs.sh" "$scripts_root")
  bash "$prereq_script"

  local cert_script
  cert_script=$(find_required_script "generate-certs.sh" "$scripts_root")
  bash "$cert_script"

  local port_script
  port_script=$(find_required_script "port-manager.sh" "$scripts_root")
  bash "$port_script" "$ports"

  local orch_script
  orch_script=$(find_required_script "stack-orchestration.sh" "$scripts_root")
  bash "$orch_script" "$bin" "$compose_file"

  local health_script
  health_script=$(find_required_script "test-health.sh" "$scripts_root")
  bash "$health_script" || true
}

execute_restart_pipeline() {
  local bin=$1
  local compose_file=$2
  local scripts_root=$3

  echo -e "${BLUE}[frontend-deployment] Restarting infrastructure stack...${NC}"
  $bin -f "$compose_file" restart
  echo -e "${GREEN}✓ Infrastructure stack restarted.${NC}"

  local health_script
  health_script=$(find_required_script "test-health.sh" "$scripts_root")
  bash "$health_script"
}

execute_down_pipeline() {
  local bin=$1
  local compose_file=$2

  echo -e "${BLUE}[frontend-deployment] Stopping infrastructure stack...${NC}"
  $bin -f "$compose_file" down
  echo -e "${GREEN}✓ All services stopped.${NC}"
}

execute_status_cmd() {
  local bin=$1
  local compose_file=$2
  $bin -f "$compose_file" ps
}

execute_logs_cmd() {
  local bin=$1
  local compose_file=$2
  shift 2
  $bin -f "$compose_file" logs -f "$@"
}

main() {
  local command=${1:-"help"}
  shift || true

  local script_dir
  script_dir=$(discover_script_dir)

  local compose_file
  compose_file=$(discover_file_upward "docker-compose.yml" "$script_dir" || echo "")

  if [ -z "$compose_file" ]; then
    echo -e "${RED}Error: Dynamic discovery could not find docker-compose.yml relative to $script_dir.${NC}"
    exit 1
  fi

  local pkg_dir
  pkg_dir=$(dirname "$compose_file")

  local scripts_root
  scripts_root=$(discover_dir_upward_containing "manage.sh" "$script_dir")

  local ports
  ports=$(get_stack_ports)

  local bin
  bin=$(get_docker_compose_cmd)

  if [ -z "$bin" ] && [[ "$command" =~ ^(up|restart|down|status|logs)$ ]]; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
  fi

  case "$command" in
    up)
      execute_up_pipeline "$bin" "$compose_file" "$scripts_root" "$ports" "$pkg_dir"
      ;;
    restart)
      execute_restart_pipeline "$bin" "$compose_file" "$scripts_root"
      ;;
    down)
      execute_down_pipeline "$bin" "$compose_file"
      ;;
    status)
      execute_status_cmd "$bin" "$compose_file"
      ;;
    logs)
      execute_logs_cmd "$bin" "$compose_file" "$@"
      ;;
    free-ports)
      local port_script
      port_script=$(find_required_script "port-manager.sh" "$scripts_root")
      bash "$port_script" "$ports"
      ;;
    health)
      local health_script
      health_script=$(find_required_script "test-health.sh" "$scripts_root")
      bash "$health_script"
      ;;
    certs)
      local cert_script
      cert_script=$(find_required_script "generate-certs.sh" "$scripts_root")
      bash "$cert_script" "$@"
      ;;
    backup-purge)
      local purge_script
      purge_script=$(find_required_script "db-backup-and-purge.sh" "$scripts_root")
      bash "$purge_script"
      ;;
    setup)
      local setup_script
      setup_script=$(find_required_script "setup.sh" "$scripts_root")
      bash "$setup_script"
      ;;
    *)
      echo "Usage: $0 {up|restart|down|status|logs|free-ports|health|certs|backup-purge|setup}"
      exit 1
      ;;
  esac
}

main "$@"
