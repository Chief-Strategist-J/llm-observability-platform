#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAFANA_DIR="$(dirname "$SCRIPT_DIR")"

# Profiles and storage
PROFILES=(development staging production)
STORAGE_DIRS=("$GRAFANA_DIR/storage/development" "$GRAFANA_DIR/storage/staging" "$GRAFANA_DIR/storage/production")
ENV_FILE_GRAFANA="$GRAFANA_DIR/grafana.env"
ENV_FILE_SECRETS="$GRAFANA_DIR/grafana-secrets.env"
COMPOSE_FILE="$GRAFANA_DIR/dashboard-grafana-compose.yaml"
IMAGE_NAME="grafana-custom:latest"

# Ensure Docker exists
ensure_docker() {
  command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }
}

# Build Docker image
build_image() {
  echo "Building Docker image $IMAGE_NAME..."
  docker build -t "$IMAGE_NAME" "$GRAFANA_DIR"
}

# Prepare host storage and env files
preflight() {
  for d in "${STORAGE_DIRS[@]}"; do
    [ -d "$d" ] || mkdir -p "$d"
    # Set permissions (use sudo if needed)
    if [ "$(id -u)" -eq 0 ]; then
      chmod 755 "$d"
      chown -R 472:472 "$d" 2>/dev/null || true
    else
      chmod 755 "$d" 2>/dev/null || sudo chmod 755 "$d" 2>/dev/null || true
      chown -R 472:472 "$d" 2>/dev/null || sudo chown -R 472:472 "$d" 2>/dev/null || true
    fi
  done

  # Create env files if they don't exist
  if [ ! -f "$ENV_FILE_GRAFANA" ]; then
    cat > "$ENV_FILE_GRAFANA" <<EOF
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=SuperSecret123!
GF_SECURITY_ALLOW_EMBEDDING=true
GF_USERS_ALLOW_SIGN_UP=false
EOF
    chmod 644 "$ENV_FILE_GRAFANA"
  fi

  if [ ! -f "$ENV_FILE_SECRETS" ]; then
    cat > "$ENV_FILE_SECRETS" <<EOF
# Additional secrets can be added here
EOF
    chmod 600 "$ENV_FILE_SECRETS"
  fi
}

# Interactive selection of profile
select_profile() {
  echo "Select profile:"
  select p in "${PROFILES[@]}" Exit; do
    case $p in
      development|staging|production) PROFILE="$p"; break ;;
      Exit) exit 0 ;;
      *) echo "Invalid option";;
    esac
  done
}

# Interactive selection of action
select_action() {
  echo "Select action:"
  select a in start stop restart logs status Exit; do
    case $a in
      start|stop|restart|logs|status) ACTION="$a"; break ;;
      Exit) exit 0 ;;
      *) echo "Invalid option";;
    esac
  done
}

# Run selected action
run_action() {
  SERVICE="grafana-$PROFILE"
  case "$ACTION" in
    start)
      docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"
      ;;
    stop)
      docker compose -f "$COMPOSE_FILE" stop "$SERVICE"
      ;;
    restart)
      docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
      ;;
    logs)
      docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
      ;;
    status)
      docker ps --filter "name=$SERVICE" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
      docker compose -f "$COMPOSE_FILE" ps
      ;;
  esac
}

main() {
  ensure_docker
  build_image
  preflight

  while true; do
    select_profile
    select_action
    run_action
    echo ""
  done
}

main
