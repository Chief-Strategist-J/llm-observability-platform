#!/usr/bin/env bash

# Database Operations & Migrations Module

cmd_db_up() {
  local compose_bin
  compose_bin=$(get_docker_compose_cmd)
  if [ -z "$compose_bin" ]; then
    log_error "Neither 'docker compose' nor 'docker-compose' is installed or accessible."
    exit 1
  fi
  if [ -f "$AUTH_DB_COMPOSE_FILE" ]; then
    log_info "Starting Auth DB container (AlloyDB / PostgreSQL on port 31412)..."
    $compose_bin -f "$AUTH_DB_COMPOSE_FILE" up -d auth-db
    log_success "Auth DB container started on port 31412."
  else
    log_error "Auth DB docker-compose.yml not found at $AUTH_DB_COMPOSE_FILE"
    exit 1
  fi
}

cmd_db_migrate() {
  log_info "Running database migration suite [ENV=${APP_ENV}]..."
  load_env_variant "$AUTH_DIR" "$APP_ENV"
  export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:31412/observability_auth}"
  cd "$AUTH_DIR"
  npx tsx database/migrate.ts
  log_success "Database migration completed."
}

cmd_db_setup() {
  log_info "Setting up database containers and executing migrations [ENV=${APP_ENV}]..."
  cmd_db_up
  log_warn "Waiting for Auth DB container readiness..."
  local retries=30
  while [ $retries -gt 0 ]; do
    if docker exec auth-service-db pg_isready -U postgres -d observability_auth >/dev/null 2>&1; then
      log_success "Auth DB container is ready."
      break
    fi
    sleep 1
    retries=$((retries - 1))
  done
  cmd_db_migrate
}
