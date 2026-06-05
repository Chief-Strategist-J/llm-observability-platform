#!/usr/bin/env bash
# entrypoint.sh: bootstrap environment for lightweight nli-worker
set -euo pipefail

# Add runtime-packages to python path if they exist
if [ -d "/runtime-packages" ]; then
    export PYTHONPATH="/app/src:/runtime-packages"
fi

# Verify if torch and transformers can be loaded
if ! python3 -c "import torch, transformers" 2>/dev/null; then
    echo "⚠️ Warning: PyTorch/Transformers not found in PYTHONPATH."
    echo "📥 Installing dynamically to container..."
    pip install --no-cache-dir "torch>=2.2.0" "transformers>=4.40.0"
fi

echo "🚀 Starting Uvicorn server..."
exec uvicorn api.rest.v1.app:app --host 0.0.0.0 --port 8009
