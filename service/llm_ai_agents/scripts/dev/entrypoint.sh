#!/bin/bash
set -e

APP_TYPE=${APP_TYPE:-bash}
MODEL_CONFIG=${MODEL_CONFIG:-llama/v3.1/gpu/8b-it}
AGENT_ID=${AGENT_ID:-default}

case "$APP_TYPE" in
  model)
    CONFIG_PATH="configs/models/local/$MODEL_CONFIG.yaml"
    python3 scripts/setup/check_system.py --config "$CONFIG_PATH"
    
    if [ $? -eq 0 ]; then
        exec bash scripts/dev/start_model.sh "$MODEL_CONFIG"
    else
        exit 1
    fi
    ;;
  agent)
    exec python3 services/agents/registry.py --id "$AGENT_ID"
    ;;
  api)
    exec python3 services/api/main.py
    ;;
  bash)
    exec /bin/bash
    ;;
  *)
    exec /bin/bash
    ;;
esac
