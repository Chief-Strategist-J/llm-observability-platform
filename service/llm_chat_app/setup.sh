#!/usr/bin/env bash
set -e

PROJECT_ROOT="/home/j/live/dinesh/llm-chatbot-python/service/llm_chat_app"
VENV_PATH="/home/j/live/dinesh/llm-chatbot-python/.venv"
ORCH_PATH="/home/j/live/dinesh/infrastructure/orchestrator"
ORCH_FILE="temporal-orchestrator-compose.yaml"

log() {
    echo -e "\n============================================"
    echo " $1"
    echo "============================================\n"
}

ask() {
    read -p "$1 (y/n): " c
    [[ "$c" == "y" ]]
}

install_if_missing() {
    local tool="$1"
    local install_cmd="$2"

    if command -v "$tool" >/dev/null 2>&1; then
        echo "$tool already installed"
    else
        echo "Installing $tool..."
        eval "$install_cmd"
    fi
}

install_core_tools() {
    sudo apt update -y
    sudo apt install -y curl wget git unzip python3 python3-pip python3-venv build-essential jq ca-certificates gnupg
}

install_docker() {
    install_if_missing "docker" "curl -fsSL https://get.docker.com | bash && sudo usermod -aG docker $USER"
}

install_clis() {
    install_if_missing "temporal" "curl -s https://temporal.download/cli.sh | bash"
    install_if_missing "railway" "bash <(curl -fsSL https://railway.app/install.sh)"
    install_if_missing "flyctl" "curl -L https://fly.io/install.sh | sh; export FLYCTL_INSTALL=\$HOME/.fly; export PATH=\$FLYCTL_INSTALL/bin:\$PATH"
    install_if_missing "render" "npm install -g render-cli"
    install_if_missing "gh" "sudo apt install -y gh"
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

    {
        echo "RENDER_API_KEY=$RENDER_API_KEY"
        echo "NEO4J_AURA_API_KEY=$NEO4J_AURA_API_KEY"
        echo "NEO4J_AURA_API_SECRET=$NEO4J_AURA_API_SECRET"
    } >> "$PROJECT_ROOT/.env.llm_chat_app"
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
    echo "These commands will open browser windows."
    ask "Continue login?" || return
    railway login
    flyctl auth login
    gh auth login
}

reset_orchestrator() {
    cd "$ORCH_PATH"
    docker compose -f "$ORCH_FILE" down -v || true
    docker system prune -f || true
    docker compose -f "$ORCH_FILE" up -d
    cd "$PROJECT_ROOT"
}

start_worker() {
    source "$VENV_PATH/bin/activate"
    python3 "$PROJECT_ROOT/worker/workers/chat_worker.py" &
}

log "LLM Chatbot Full Setup"

ask "Install core tools?" && install_core_tools
ask "Install Docker?" && install_docker
ask "Install CLI tools?" && install_clis
ask "Setup Python environment?" && setup_python
ask "Provide API Keys?" && ask_for_api_keys
ask "Load environment variables?" && load_env
ask "Login to all platforms?" && platform_logins
ask "Reset Temporal Orchestrator?" && reset_orchestrator
ask "Start Temporal Worker?" && start_worker

log "Setup Completed Successfully!"
echo "Run workflows using triggers."
