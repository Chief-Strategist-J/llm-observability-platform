"""
AI Agents Service — Single Entry Point

Usage:
    python run.py

Starts the FastAPI server with all agents, workflows, and model
management endpoints. This is the only command you need.
"""
import sys
import os

# Ensure the service root is on sys.path so imports like
# `from config.settings import ...` resolve correctly.
SERVICE_ROOT = os.path.dirname(os.path.abspath(__file__))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

import uvicorn
from config.settings import API_HOST, API_PORT
from gateway.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "run:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        reload_dirs=[SERVICE_ROOT],
    )
