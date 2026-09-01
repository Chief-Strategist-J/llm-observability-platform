#!/usr/bin/env bash

# Environment & Default Values Configuration

APP_ENV="${APP_ENV:-${NODE_ENV:-development}}"

# Core Service Ports
PORT_UNIT="${PORT_UNIT:-${PORT:-31400}}"
PORT_AUTH="${PORT_AUTH:-3001}"
PORT_STORYBOOK="${PORT_STORYBOOK:-31406}"
PORT_KAFKA="${PORT_KAFKA:-31414}"

# Python Microservices Unique Ports
PORT_LATENCY="${PORT_LATENCY:-8003}"
PORT_ALERT="${PORT_ALERT:-8004}"
PORT_QUALITY="${PORT_QUALITY:-8005}"
PORT_FAITHFULNESS="${PORT_FAITHFULNESS:-8006}"
PORT_PERPLEXITY="${PORT_PERPLEXITY:-8007}"
PORT_TOXICITY="${PORT_TOXICITY:-8008}"
PORT_NLI="${PORT_NLI:-8009}"
PORT_EMBEDDING="${PORT_EMBEDDING:-8010}"
PORT_COHERENCE="${PORT_COHERENCE:-8011}"
PORT_SLO="${PORT_SLO:-8012}"
PORT_EWMA="${PORT_EWMA:-8013}"
PORT_BUDGET="${PORT_BUDGET:-8014}"
PORT_EVENT_COST="${PORT_EVENT_COST:-8015}"
PORT_FORECAST="${PORT_FORECAST:-8017}"

# Directories Calculation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
AUTH_DIR="$(dirname "$APP_DIR")/auth"
PYTHON_ROOT="$(cd "$APP_DIR/../../python" 2>/dev/null && pwd || echo "$(dirname "$(dirname "$APP_DIR")")/python")"

LATENCY_DIR="${PYTHON_ROOT}/latency-engine"
ALERT_DIR="${PYTHON_ROOT}/alert-engine"
QUALITY_DIR="${PYTHON_ROOT}/quality-engine"
FAITHFULNESS_DIR="${PYTHON_ROOT}/faithfulness"
PERPLEXITY_DIR="${PYTHON_ROOT}/perplexity"
TOXICITY_DIR="${PYTHON_ROOT}/toxicity"
NLI_DIR="${PYTHON_ROOT}/nli-worker"
EMBEDDING_DIR="${PYTHON_ROOT}/queue-embedding-worker"
COHERENCE_DIR="${PYTHON_ROOT}/semantic-coherence"
SLO_DIR="${PYTHON_ROOT}/slo-burn-worker"
EWMA_DIR="${PYTHON_ROOT}/temporal-ewma-worker"
BUDGET_DIR="${PYTHON_ROOT}/budget-provisioner"
EVENT_COST_DIR="${PYTHON_ROOT}/event-cost"
FORECAST_DIR="${PYTHON_ROOT}/forecast-worker"

DEPLOYMENT_DIR="$(dirname "$APP_DIR")/frontend-deployment"
AUTH_COMPOSE_FILE="$DEPLOYMENT_DIR/docker-compose.yml"
AUTH_DB_COMPOSE_FILE="$AUTH_DIR/docker-compose.yml"
