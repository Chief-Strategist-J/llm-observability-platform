#!/bin/bash
set -e

MODEL_CONFIG=${1:-llama/v3.1/gpu/8b-it}
CONFIG_PATH="configs/models/local/$MODEL_CONFIG.yaml"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$DIR")")"

cd "$PROJECT_ROOT"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

if [ ! -f "$CONFIG_PATH" ]; then
    exit 1
fi

python3 scripts/dev/run_model.py --config "$CONFIG_PATH"
