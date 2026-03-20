#!/bin/bash
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/infrastructure/observability/dependencies/venv/bin/python3"
PORT=8103
TRAEFIK_DIR="${PROJECT_ROOT}/infrastructure/orchestrator/config/docker/traefik/config"
TEMPORAL_COMPOSE="${PROJECT_ROOT}/infrastructure/orchestrator/config/docker/temporal/temporal-orchestrator-compose.yaml"

echo "--- 1. Port & Service Cleanup ---"
if command -v lsof >/dev/null 2>&1; then
    for p in 80 443 8103 7233; do
        PID=$(lsof -t -i:$p)
        if [ -n "$PID" ]; then
            echo "Clearing port $p (PID $PID)..."
            kill -9 "$PID" 2>/dev/null
        fi
    done
fi
sudo systemctl stop apache2 2>/dev/null || true

echo "--- 2. Docker Infrastructure Bootstrap ---"
cd "$PROJECT_ROOT"
networks=("observability-network" "data-network" "messaging-network" "cicd-network" "temporal-network" "database-network")
for net in "${networks[@]}"; do
    sudo docker network inspect "$net" >/dev/null 2>&1 || sudo docker network create "$net"
done

echo "--- 3. Traefik & Temporal Setup ---"
mkdir -p "${TRAEFIK_DIR}/tls"
cat <<EOF > "${TRAEFIK_DIR}/tls/scaibu.observability-api.yml"
http:
  routers:
    observability-api:
      rule: "Host(\`scaibu.observability-api\`)"
      service: observability-api-service
      entryPoints: [web]
  services:
    observability-api-service:
      loadBalancer:
        servers: [{url: "http://172.28.0.1:8103"}]
EOF

sudo docker compose -f "${TRAEFIK_DIR}/traefik-dynamic-docker.yaml" up -d
sudo docker compose -f "$TEMPORAL_COMPOSE" up -d

echo "--- 4. Dependency & Module Verification ---"
"${PROJECT_ROOT}/infrastructure/observability/dependencies/install_deps.sh" || exit 1

echo "--- 5. Starting Orchestrator Worker & Service API ---"
if [ ! -f "$VENV_PYTHON" ]; then VENV_PYTHON="python3"; fi
echo "Waiting for Temporal (port 7233)..."
for i in {1..30}; do
    if lsof -i:7233 >/dev/null 2>&1; then break; fi
    sleep 2
done

# Start worker with sudo for Docker access
sudo PYTHONPATH="$PROJECT_ROOT" "$VENV_PYTHON" -m infrastructure.orchestrator.base.docker_orchestrator_worker > worker.log 2>&1 &
WORKER_PID=$!
# Start API (can stay as user)
nohup "$VENV_PYTHON" -m infrastructure.observability.api.service_api > observability_api.log 2>&1 &
API_PID=$!

echo "Waiting for API to bind to $PORT..."
for i in {1..20}; do
    if lsof -i:$PORT >/dev/null 2>&1; then
        echo "API is LIVE. Triggering automated bootstrap..."
        sleep 5
        curl -s -X POST http://127.0.0.1:8103/start >/dev/null
        echo "--- SETUP COMPLETE ---"
        echo "Access Grafana: http://scaibu.grafana"
        echo "Access API: http://scaibu.observability-api/status"
        exit 0
    fi
    sleep 1
done

echo "Failed to start API."
kill -9 $API_PID 2>/dev/null
sudo kill -9 $WORKER_PID 2>/dev/null
exit 1
