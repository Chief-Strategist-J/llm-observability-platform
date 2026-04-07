#!/bin/bash
set -e

MODEL_ID=$1
if [ -z "$MODEL_ID" ]; then
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$DIR")")"

if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

if ! command -v huggingface-cli &> /dev/null; then
    python3 -m pip install -U "huggingface_hub[cli]"
fi

python3 -m huggingface_hub.commands.huggingface_cli download "$MODEL_ID"
