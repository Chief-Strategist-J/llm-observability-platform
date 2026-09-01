#!/usr/bin/env bash

# Service Dispatcher & Dev Environment Orchestrator

cmd_list_services() {
  log_header "REGISTERED SERVICE CATALOG [ENV=${APP_ENV}]:"
  printf " %-12s | %-6s | %-25s | %s\n" "KEY" "PORT" "NAME" "DIRECTORY"
  echo "----------------------------------------------------------------------"
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    printf " %-12s | %-6s | %-25s | %s\n" "$key" "$port" "$name" "$dir"
  done
  log_info "===================================================="
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
          log_warn "Auth DB (port 31412) is offline. Automatically starting DB and running migrations..."
          cmd_db_setup
        fi
      fi
      if [ "$key" != "kafka" ]; then
        free_port "$port"
      fi
      log_success "Starting ${BOLD}${name}${NC} on port ${BOLD}${port}${NC} [ENV=${APP_ENV}]..."
      cd "$dir"
      eval "$cmd"
      break
    fi
  done

  if [ "$found" = false ]; then
    log_error "Service '${target_key}' not found in Service Registry."
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
    log_info "Cleaning up previous web-app image..."
    docker image rm web-app-web-app --force >/dev/null 2>&1 || true
    log_info "Freeing port 31400 and starting Next.js Web App in Docker Compose (Hot Reload Enabled)..."
    free_port 31400
    exec docker compose up --build
  fi

  log_info "Preparing development environment [ENV=${APP_ENV}]..."
  if [ ! -f ".env.local" ] && [ -f ".env.local.example" ]; then
    cp .env.local.example .env.local
  fi

  for service_key in "${target_services[@]}"; do
    if [ "$service_key" = "auth" ]; then
      if ! nc -z localhost 31412 >/dev/null 2>&1; then
        log_warn "Auth DB (port 31412) is offline. Automatically starting DB and running migrations..."
        cmd_db_setup
      fi
    fi
  done

  clean_deep_artifacts
  cmd_install_deps

  log_header "FIXED SERVICE ENDPOINTS [ENV=${APP_ENV}]:"
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
  log_info "===================================================="

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
