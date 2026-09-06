#!/usr/bin/env bash

# Utility Helper Functions

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

free_port() {
  local port=$1
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -i:"${port}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      log_warn "Terminating process(es) on port ${port}: ${pids}"
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

free_all_registered_ports() {
  log_info "Freeing ports for all registered services..."
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    if [ "$key" != "kafka" ]; then
      free_port "$port"
    fi
  done
  log_success "All registered service ports freed/verified."
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

  status_code=$(curl -s -m 3 --connect-timeout 2 -o /dev/null -w "%{http_code}" "$url" || echo "000")

  if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 400 ]; then
    echo -e "  ${GREEN}[ONLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  elif [ "$status_code" = "404" ] || [ "$status_code" = "401" ] || [ "$status_code" = "405" ]; then
    echo -e "  ${GREEN}[ONLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  else
    echo -e "  ${RED}[OFFLINE]${NC} ${BOLD}$name${NC} -> $url (HTTP $status_code)"
  fi
}
