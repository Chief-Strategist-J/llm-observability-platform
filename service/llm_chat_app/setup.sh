#!/bin/bash
set -e

PROJECT_ROOT="/home/j/live/dinesh/llm-chatbot-python/service/llm_chat_app"
VENV_PATH="/home/j/live/dinesh/llm-chatbot-python/.venv"
ORCH_PATH="/home/j/live/dinesh/infrastructure/orchestrator"
ORCH_FILE="temporal-orchestrator-compose.yaml"

log() {
    echo ""
    echo "============================================"
    echo " $1"
    echo "============================================"
    echo ""
}

ask() {
    read -p "$1 (y/n): " c
    if [ "$c" != "y" ]; then return 1; fi
    return 0
}

install_core_tools() {
    sudo apt update -y
    sudo apt install -y curl wget git unzip python3 python3-pip python3-venv build-essential jq
}

install_docker() {
    if ! command -v docker >/dev/null; then
        curl -fsSL https://get.docker.com | bash
        sudo usermod -aG docker $USER
    fi
}

install_clis() {
    if ! command -v temporal >/dev/null; then
        curl -s https://temporal.download/cli.sh | bash
    fi
    if ! command -v railway >/dev/null; then
        bash <(curl -fsSL https://railway.app/install.sh)
    fi
    if ! command -v fly >/dev/null; then
        curl -L https://fly.io/install.sh | sh
        export FLYCTL_INSTALL="$HOME/.fly"
        export PATH="$FLYCTL_INSTALL/bin:$PATH"
    fi
    if ! command -v render >/dev/null; then
        npm install -g render-cli || true
    fi
    if ! command -v gh >/dev/null; then
        sudo apt install -y gh
    fi
}

setup_python() {
    if [ ! -d "$VENV_PATH" ]; then
        python3 -m venv "$VENV_PATH"
    fi

    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
}

ask_for_api_keys() {
    read -p "Enter Render API Key: " RENDER_API_KEY
    read -p "Enter Neo4j Aura API Key: " NEO4J_AURA_API_KEY
    read -p "Enter Neo4j Aura API Secret: " NEO4J_AURA_API_SECRET

    echo "RENDER_API_KEY=$RENDER_API_KEY" >> "$PROJECT_ROOT/.env.llm_chat_app"
    echo "NEO4J_AURA_API_KEY=$NEO4J_AURA_API_KEY" >> "$PROJECT_ROOT/.env.llm_chat_app"
    echo "NEO4J_AURA_API_SECRET=$NEO4J_AURA_API_SECRET" >> "$PROJECT_ROOT/.env.llm_chat_app"
}

load_env() {
    if [ -f "$PROJECT_ROOT/.env.llm_chat_app" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env.llm_chat_app" | xargs)
    fi
    if [ -f "$PROJECT_ROOT/.env.chat" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env.chat" | xargs)
    fi
}

platform_logins() {
    railway login
    fly auth login
    gh auth login
}

reset_orchestrator() {
    cd "$ORCH_PATH"
    docker-compose -f "$ORCH_FILE" down -v || true
    docker system prune -f || true
    docker-compose -f "$ORCH_FILE" up -d
    cd "$PROJECT_ROOT"
}

start_worker() {
    source "$VENV_PATH/bin/activate"
    python3 "$PROJECT_ROOT/worker/workers/chat_worker.py" &
}

log "LLM Chatbot Full Setup"

if ask "Install core tools?"; then install_core_tools; fi
if ask "Install Docker?"; then install_docker; fi
if ask "Install CLI tools?"; then install_clis; fi
if ask "Setup Python environment?"; then setup_python; fi
if ask "Provide API Keys?"; then ask_for_api_keys; fi
if ask "Load environment variables?"; then load_env; fi
if ask "Login to all platforms?"; then platform_logins; fi
if ask "Reset Temporal Orchestrator?"; then reset_orchestrator; fi
if ask "Start Temporal Worker?"; then start_worker; fi

log "Setup Completed"
echo "Run workflows using triggers."
