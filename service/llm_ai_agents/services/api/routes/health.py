from flask import Blueprint, jsonify
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def index():
    """Root index endpoint"""
    return jsonify({
        "message": "LLM Observability Platform API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat_completions": "/v1/chat/completions",
            "docs": "See /health for status"
        }
    })

@health_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "model": os.getenv("MODEL_ID", "gemma-2-2b"),
        "service": "llm-observability-platform"
    })

@health_bp.route('/api/status', methods=['GET'])
def status():
    """Detailed status endpoint"""
    return jsonify({
        "status": "running",
        "model": os.getenv("MODEL_ID", "gemma-2-2b"),
        "service": "llm-observability-platform",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "health": "/health",
            "simple_chat": "/api/chat"
        }
    })
