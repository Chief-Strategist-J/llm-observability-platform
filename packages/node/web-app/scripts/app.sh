#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Centralized Structured Logger
source "$SCRIPT_DIR/lib/logger.sh"

# 2. Configurations (Environment & Service Catalog Data)
source "$SCRIPT_DIR/config/env.sh"
source "$SCRIPT_DIR/config/service_registry.sh"

# 3. Functional Logic Modules
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/clean.sh"
source "$SCRIPT_DIR/lib/docker.sh"
source "$SCRIPT_DIR/lib/db.sh"
source "$SCRIPT_DIR/lib/health.sh"
source "$SCRIPT_DIR/lib/service_runner.sh"
source "$SCRIPT_DIR/lib/build.sh"

# 4. Global Flag Parsing
COMMAND=${1:-"help"}
shift || true

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --env=*)
      APP_ENV="${1#*=}"
      shift
      ;;
    --env|-e)
      APP_ENV="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

# 5. CLI Command Router Dispatcher
case "$COMMAND" in
  clean)
    clean_build_artifacts
    ;;
  clean-all)
    clean_deep_artifacts
    ;;
  free-ports)
    if [ "$#" -gt 0 ]; then
      for port in "$@"; do
        free_port "$port"
      done
    else
      free_all_registered_ports
    fi
    ;;
  list|services)
    cmd_list_services
    ;;
  run|service)
    cmd_run_service "$1"
    ;;
  dev)
    cmd_dev "$@"
    ;;
  auth)
    cmd_run_service "auth"
    ;;
  web-app)
    cmd_run_service "web-app"
    ;;
  storybook)
    cmd_run_service "storybook"
    ;;
  latency|latency-engine)
    cmd_run_service "latency-engine"
    ;;
  kafka)
    cmd_run_service "kafka"
    ;;
  db:up|db-up)
    cmd_db_up
    ;;
  db:migrate|db-migrate)
    cmd_db_migrate
    ;;
  db:setup|db-setup)
    cmd_db_setup
    ;;
  build-verify)
    cmd_build_verify
    ;;
  health)
    cmd_health
    ;;
  docker-up)
    cmd_docker_up
    ;;
  docker-down)
    cmd_docker_down
    ;;
  docker-status)
    cmd_docker_status
    ;;
  docker-logs)
    cmd_docker_logs "$@"
    ;;
  install-deps)
    cmd_install_deps "$@"
    ;;
  *)
    log_info "Usage: $0 {list|run <service>|dev [services...]|auth|web-app|storybook|latency-engine|kafka|db:migrate|db:setup|clean|free-ports|health|docker-up|docker-down|docker-status|docker-logs}"
    exit 1
    ;;
esac
