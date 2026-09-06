#!/usr/bin/env bash

# Docker Compose Management Module

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
    log_error "Neither 'docker compose' nor 'docker-compose' is installed or accessible."
    exit 1
  fi
  log_info "Starting infra container services (Traefik, Redis, Kafka, Tempo, Grafana)..."
  $compose_bin -f "$AUTH_COMPOSE_FILE" up -d
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    log_info "Starting Auth DB container service (AlloyDB / PostgreSQL on port 31412)..."
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" up -d auth-db
  fi
  log_success "All container services (Infra + Auth DB) started successfully."
}

cmd_docker_down() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    log_error "Neither 'docker compose' nor 'docker-compose' is installed or accessible."
    exit 1
  fi
  log_info "Stopping all container services..."
  $compose_bin -f "$AUTH_COMPOSE_FILE" down
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" down
  fi
  log_success "All container services stopped."
}

cmd_docker_status() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    log_error "Neither 'docker compose' nor 'docker-compose' is installed or accessible."
    exit 1
  fi
  log_info "--- Infra Services Status ---"
  $compose_bin -f "$AUTH_COMPOSE_FILE" ps
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    log_info "--- Auth Database Status ---"
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" ps
  fi
}

cmd_docker_logs() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    log_error "Neither 'docker compose' nor 'docker-compose' is installed or accessible."
    exit 1
  fi
  $compose_bin -f "$AUTH_COMPOSE_FILE" logs -f "$@"
}
