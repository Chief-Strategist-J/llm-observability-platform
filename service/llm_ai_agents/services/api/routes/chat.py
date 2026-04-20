from flask import Blueprint, request, jsonify, Response
import json
import os
from services.llm.factory import LLMFactory
from services.shared.config_loader import load_yaml_config
from services.shared.cache import instance_cache

chat_bp = Blueprint("chat", __name__)

_DEFAULT_CONFIG = os.getenv(
    "MODEL_CONFIG",
    "configs/models/local/gemma/v2/cpu/2b-cpu-only.yaml",
)


def _get_llm_instance(config_path: str = None):
    key = f"llm_instance:{config_path or _DEFAULT_CONFIG}"
    cached = instance_cache.get(key)
    if cached is not None:
        return cached
    config = load_yaml_config(config_path or _DEFAULT_CONFIG)
    llm = LLMFactory.create(config)
    instance_cache.set(key, llm)
    return llm


def _call_llm(instance, prompt: str, params: dict) -> str:
    return instance.generate(prompt, **params)


def _call_stream(instance, prompt: str, params: dict):
    return instance.stream_generate(prompt, **params)


def _build_params(data: dict) -> dict:
    return {
        "temperature": data.get("temperature", 0.7),
        "top_p": data.get("top_p", 0.95),
        "max_tokens": data.get("max_tokens", 512),
    }


def _extract_prompt(data: dict) -> str:
    prompt = data.get("prompt")
    if prompt:
        return prompt
    messages = data.get("messages", [])
    if isinstance(messages, list) and messages:
        return messages[-1].get("content", "")
    return ""


def _stream_response(instance, prompt: str, params: dict) -> Response:
    def generate():
        try:
            for chunk in _call_stream(instance, prompt, params):
                if chunk:
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}, 'index': 0, 'finish_reason': None}]})}\n\n"
            yield f"data: {json.dumps({'choices': [{'delta': {}, 'index': 0, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


@chat_bp.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.get_json(silent=True) or {}
    prompt = _extract_prompt(data)
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    try:
        instance = _get_llm_instance(data.get("config_path"))
        params = _build_params(data)
        if data.get("stream", False):
            return _stream_response(instance, prompt, params)
        response = _call_llm(instance, prompt, params)
        return jsonify({
            "choices": [{
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop",
                "index": 0,
            }]
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    try:
        instance = _get_llm_instance(data.get("config_path"))
        response = _call_llm(instance, prompt, _build_params(data))
        return jsonify({"response": response, "status": "success"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
