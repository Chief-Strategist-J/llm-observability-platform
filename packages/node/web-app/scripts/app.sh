#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

APP_ENV="${APP_ENV:-${NODE_ENV:-development}}"

PORT_UNIT="${PORT_UNIT:-${PORT:-31400}}"
PORT_AUTH="${PORT_AUTH:-3001}"
PORT_STORYBOOK="${PORT_STORYBOOK:-31406}"
PORT_KAFKA="${PORT_KAFKA:-31414}"
PORT_LATENCY="${PORT_LATENCY:-8003}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
AUTH_DIR="$(dirname "$APP_DIR")/auth"
LATENCY_DIR="$(cd "$APP_DIR/../../python/latency-engine" 2>/dev/null && pwd || echo "$(dirname "$(dirname "$APP_DIR")")/python/latency-engine")"
DEPLOYMENT_DIR="$(dirname "$APP_DIR")/frontend-deployment"
AUTH_COMPOSE_FILE="$DEPLOYMENT_DIR/docker-compose.yml"
AUTH_DB_COMPOSE_FILE="$AUTH_DIR/docker-compose.yml"

SERVICE_REGISTRY=(
  "web-app:Next.js Web Application:${PORT_UNIT}:${APP_DIR}:PORT=${PORT_UNIT} npx next dev -p ${PORT_UNIT}"
  "auth:Auth HTTP Service:${PORT_AUTH}:${AUTH_DIR}:PORT=${PORT_AUTH} npx tsx src/server.ts"
  "storybook:Storybook Server:${PORT_STORYBOOK}:${APP_DIR}:npx storybook dev -p ${PORT_STORYBOOK}"
  "latency-engine:Latency Engine Worker & API:${PORT_LATENCY}:${LATENCY_DIR}:${LATENCY_DIR}/scripts/run.sh"
  "latency:Latency Engine Worker & API:${PORT_LATENCY}:${LATENCY_DIR}:${LATENCY_DIR}/scripts/run.sh"
)

BUILD_TARGETS=(
  ".next"
  "storybook-static"
  "tsconfig.tsbuildinfo"
  ".cache"
  "coverage"
  ".vitest"
)

DEEP_TARGETS=(
  "node_modules"
  "package-lock.json"
)

ensure_app_dir() {
  cd "$APP_DIR"
}

load_env_variant() {
  local target_dir=$1
  local env_name=$2
  local files=(
    "${target_dir}/.env.${env_name}.local"
    "${target_dir}/.env.${env_name}"
    "${target_dir}/.env.local"
    "${target_dir}/.env"
  )
  for file in "${files[@]}"; do
    if [ -f "$file" ]; then
      set -o allexport
      source "$file"
      set +o allexport
    fi
  done
  export NODE_ENV="$env_name"
  export APP_ENV="$env_name"
}

remove_target() {
  local target=$1
  if [ -e "$target" ]; then
    echo -e "${YELLOW}  - Removing $target${NC}"
    rm -rf "$target"
  fi
}

clean_build_artifacts() {
  ensure_app_dir
  echo -e "${BLUE}[web-app] Cleaning build artifacts...${NC}"
  for target in "${BUILD_TARGETS[@]}"; do
    remove_target "$target"
  done
  echo -e "${GREEN}✓ Clean completed successfully.${NC}"
}

clean_deep_artifacts() {
  ensure_app_dir
  clean_build_artifacts
  echo -e "${BLUE}[web-app] Performing deep clean...${NC}"
  for target in "${DEEP_TARGETS[@]}"; do
    if [ -e "$target" ]; then
      echo -e "${RED}  - Removing $target${NC}"
      rm -rf "$target"
    fi
  done
  echo -e "${GREEN}✓ Deep clean completed successfully.${NC}"
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

free_all_registered_ports() {
  echo -e "${BLUE}[registry] Freeing ports for all registered services...${NC}"
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    if [ "$key" != "kafka" ]; then
      free_port "$port"
    fi
  done
  echo -e "${GREEN}✓ All registered service ports freed/verified.${NC}"
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

cmd_docker_up() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is installed or accessible.${NC}"
    exit 1
  fi
  echo -e "${BLUE}[docker] Starting infra container services (Traefik, Redis, Kafka, Tempo, Grafana)...${NC}"
  $compose_bin -f "$AUTH_COMPOSE_FILE" up -d
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    echo -e "${BLUE}[docker] Starting Auth DB container service (AlloyDB / PostgreSQL on port 31412)...${NC}"
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" up -d auth-db
  fi
  echo -e "${GREEN}✓ All container services (Infra + Auth DB) started successfully.${NC}"
}

cmd_docker_down() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is installed or accessible.${NC}"
    exit 1
  fi
  echo -e "${BLUE}[docker] Stopping all container services...${NC}"
  $compose_bin -f "$AUTH_COMPOSE_FILE" down
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" down
  fi
  echo -e "${GREEN}✓ All container services stopped.${NC}"
}

cmd_docker_status() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is installed or accessible.${NC}"
    exit 1
  fi
  echo -e "${BLUE}--- Infra Services Status ---${NC}"
  $compose_bin -f "$AUTH_COMPOSE_FILE" ps
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    echo -e "${BLUE}--- Auth Database Status ---${NC}"
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" ps
  fi
}

cmd_docker_logs() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is installed or accessible.${NC}"
    exit 1
  fi
  $compose_bin -f "$AUTH_COMPOSE_FILE" logs -f "$@"
}

cmd_db_up() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is installed or accessible.${NC}"
    exit 1
  fi
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    echo -e "${BLUE}[db] Starting Auth DB container (AlloyDB / PostgreSQL on port 31412)...${NC}"
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" up -d auth-db
    echo -e "${GREEN}✓ Auth DB container started on port 31412.${NC}"
  else
    echo -e "${RED}Error: Auth DB docker-compose.yml not found at $AUTH_DB_COMPOSE_FILE${NC}"
    exit 1
  fi
}

cmd_db_migrate() {
  echo -e "${BLUE}[db] Running database migration suite [ENV=${APP_ENV}]...${NC}"
  load_env_variant "$AUTH_DIR" "$APP_ENV"
  export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:31412/observability_auth}"
  cd "$AUTH_DIR"
  npx tsx database/migrate.ts
  echo -e "${GREEN}✓ Database migration completed.${NC}"
}

cmd_db_setup() {
  echo -e "${BLUE}[db] Setting up database containers and executing migrations [ENV=${APP_ENV}]...${NC}"
  cmd_db_up
  echo -e "${YELLOW}[db] Waiting for Auth DB container readiness...${NC}"
  local retries=30
  while [ $retries -gt 0 ]; do
    if docker exec auth-service-db pg_isready -U postgres -d observability_auth >/dev/null 2>&1; then
      echo -e "${GREEN}✓ Auth DB container is ready.${NC}"
      break
    fi
    sleep 1
    retries=$((retries - 1))
  done
  cmd_db_migrate
}

check_tcp_port() {
  local name=$1
  local port=$2
  if nc -z localhost "$port" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[ONLINE]${NC} ${BOLD}$name${NC} -> localhost:$port (TCP OPEN)"
  else
    echo -e "  ${RED}[OFFLINE]${NC} ${BOLD}$name${NC} -> localhost:$port (TCP CLOSED)"
  fi
}

check_http_service() {
  local name=$1
  local url=$2
  local status_code

  status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

  if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 400 ]; then
    echo -e "  ${GREEN}[ONLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  elif [ "$status_code" = "404" ] || [ "$status_code" = "401" ] || [ "$status_code" = "405" ]; then
    echo -e "  ${GREEN}[ONLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  else
    echo -e "  ${RED}[OFFLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  fi
}

cmd_health() {
  echo -e "${BLUE}[health] Performing health check across registered services [ENV=${APP_ENV}]...${NC}"
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    if [ "$key" = "auth" ]; then
      check_http_service "$name" "http://localhost:${port}/health"
    elif [ "$key" = "kafka" ]; then
      check_tcp_port "$name" "$port"
    else
      check_http_service "$name" "http://localhost:${port}"
    fi
  done
}

cmd_list_services() {
  echo -e "${BLUE}====================================================${NC}"
  echo -e "${BOLD} REGISTERED SERVICE CATALOG [ENV=${APP_ENV}]:${NC}"
  echo -e "${BLUE}====================================================${NC}"
  printf " %-12s | %-6s | %-25s | %s\n" "KEY" "PORT" "NAME" "DIRECTORY"
  echo "----------------------------------------------------------------------"
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    printf " %-12s | %-6s | %-25s | %s\n" "$key" "$port" "$name" "$dir"
  done
  echo -e "${BLUE}====================================================${NC}"
}

cmd_run_service() {
  local target_key=$1
  local found=false

  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    if [ "$key" = "$target_key" ]; then
      found=true
      load_env_variant "$dir" "$APP_ENV"
      if [ "$key" = "auth" ]; then
        if ! nc -z localhost 31412 >/dev/null 2>&1; then
          echo -e "${YELLOW}[service-runner] Auth DB (port 31412) is offline. Automatically starting DB and running migrations...${NC}"
          cmd_db_setup
        fi
      fi
      if [ "$key" != "kafka" ]; then
        free_port "$port"
      fi
      echo -e "${GREEN}[service-runner] Starting ${BOLD}${name}${NC} on port ${BOLD}${port}${NC} [ENV=${APP_ENV}]..."
      cd "$dir"
      eval "$cmd"
      break
    fi
  done

  if [ "$found" = false ]; then
    echo -e "${RED}Error: Service '${target_key}' not found in Service Registry.${NC}"
    cmd_list_services
    exit 1
  fi
}

cmd_dev() {
  ensure_app_dir
  local target_services=("$@")

  if [ "${#target_services[@]}" -eq 0 ]; then
    target_services=("web-app" "auth" "storybook")
  elif [ "${#target_services[@]}" -eq 1 ] && [ "${target_services[0]}" = "all" ]; then
    target_services=("web-app" "auth" "storybook" "latency-engine")
  fi

  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f "docker-compose.yaml" ]; then
    echo -e "${BLUE}[dev-orchestrator] Cleaning up previous web-app image...${NC}"
    docker image rm web-app-web-app --force >/dev/null 2>&1 || true
    echo -e "${BLUE}[dev-orchestrator] Freeing port 31400 and starting Next.js Web App in Docker Compose (Hot Reload Enabled)...${NC}"
    free_port 31400
    exec docker compose up --build
  fi

  echo -e "${BLUE}[dev-orchestrator] Preparing development environment [ENV=${APP_ENV}]...${NC}"
  if [ ! -f ".env.local" ] && [ -f ".env.local.example" ]; then
    cp .env.local.example .env.local
  fi

  for service_key in "${target_services[@]}"; do
    if [ "$service_key" = "auth" ]; then
      if ! nc -z localhost 31412 >/dev/null 2>&1; then
        echo -e "${YELLOW}[dev-orchestrator] Auth DB (port 31412) is offline. Automatically starting DB and running migrations...${NC}"
        cmd_db_setup
      fi
    fi
  done

  clean_deep_artifacts
  cmd_install_deps

  echo -e "${GREEN}====================================================${NC}"
  echo -e "${GREEN} FIXED SERVICE ENDPOINTS [ENV=${APP_ENV}]:${NC}"
  for service_key in "${target_services[@]}"; do
    for entry in "${SERVICE_REGISTRY[@]}"; do
      IFS=':' read -r key name port dir cmd <<< "$entry"
      if [ "$key" = "$service_key" ]; then
        if [ "$key" != "kafka" ]; then
          free_port "$port"
        fi
        echo -e "   - ${BOLD}${name} (${key})${NC}: http://localhost:${port}"
      fi
    done
  done
  echo -e "${GREEN}====================================================${NC}"

  local exec_cmds=()
  for service_key in "${target_services[@]}"; do
    for entry in "${SERVICE_REGISTRY[@]}"; do
      IFS=':' read -r key name port dir cmd <<< "$entry"
      if [ "$key" = "$service_key" ]; then
        exec_cmds+=("(cd \"$dir\" && load_env_variant \"$dir\" \"$APP_ENV\" && $cmd)")
      fi
    done
  done

  local combined_cmd=""
  for i in "${!exec_cmds[@]}"; do
    if [ "$i" -eq 0 ]; then
      combined_cmd="${exec_cmds[$i]}"
    else
      combined_cmd="${combined_cmd} & ${exec_cmds[$i]}"
    fi
  done

  eval "($combined_cmd)"
}

cmd_install_deps() {
  ensure_app_dir
  if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
    clean_deep_artifacts
  fi
  echo -e "${BLUE}[web-app] Installing and updating dependencies...${NC}"
  npm install && npm update
  echo -e "${GREEN}✓ Dependencies installed and updated successfully.${NC}"
}

cmd_build_verify() {
  ensure_app_dir
  echo -e "${BLUE}[web-app] Running build verification pipeline...${NC}"
  clean_build_artifacts
  echo -e "${YELLOW}Running typecheck...${NC}"
  npx tsc --noEmit
  echo -e "${YELLOW}Running lint...${NC}"
  npx eslint
  echo -e "${YELLOW}Building Next.js app...${NC}"
  npx next build
  echo -e "${GREEN}✓ Verification completed successfully!${NC}"
}

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
    echo "Usage: $0 {list|run <service>|dev [services...]|auth|web-app|storybook|latency-engine|kafka|db:migrate|db:setup|clean|free-ports|health|docker-up|docker-down|docker-status|docker-logs}"
    exit 1
    ;;
esac
