#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INFRASTRUCTURE_DIR="$(cd "$PROJECT_ROOT/../../code-quality" && pwd)"
source "$SCRIPT_DIR/utils.sh"

DOCKER_COMPOSE_FILE="$INFRASTRUCTURE_DIR/deployment/docker/docker-compose.optimized.yml"
SONAR_SERVICE="sonarqube"

is_server_running() {
  if ! check_command "docker"; then
    log_error "Docker is not installed or not in PATH"
    return 2
  fi

  if ! check_command "docker-compose"; then
    log_error "docker-compose is not installed or not in PATH"
    return 2
  fi

  if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
    return 2
  fi

  cd "$INFRASTRUCTURE_DIR"
  local status
  status=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q "$SONAR_SERVICE" 2>/dev/null)

  if [[ -n "$status" ]]; then
    log_info "SonarQube server is running"
    return 0
  else
    log_info "SonarQube server is not running"
    return 1
  fi
}

start_server() {
  log_info "Starting SonarQube server..."

  if is_server_running; then
    log_success "SonarQube server is already running"
    return 0
  fi

  cd "$INFRASTRUCTURE_DIR"
  if docker-compose -f "$DOCKER_COMPOSE_FILE" up -d "$SONAR_SERVICE"; then
    log_success "SonarQube server started successfully"
    log_info "Waiting for SonarQube to be ready..."
    sleep 30
    return 0
  else
    log_error "Failed to start SonarQube server"
    return 1
  fi
}

stop_server() {
  log_info "Stopping SonarQube server..."

  if ! is_server_running; then
    log_info "SonarQube server is not running"
    return 0
  fi

  cd "$INFRASTRUCTURE_DIR"
  if docker-compose -f "$DOCKER_COMPOSE_FILE" stop "$SONAR_SERVICE"; then
    log_success "SonarQube server stopped successfully"
    return 0
  else
    log_error "Failed to stop SonarQube server"
    return 1
  fi
}

get_server_url() {
  echo "http://localhost:9000"
}
