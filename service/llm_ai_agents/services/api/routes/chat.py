from flask import Blueprint, request, jsonify
import sys
import os

# Add parent directory to path to import services
# Add project root to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from services.llm.factory import LLMFactory
import yaml

chat_bp = Blueprint('chat', __name__)

llm_instance = None

def get_llm_instance(config_path=None):
    global llm_instance
    if llm_instance is not None:
        return llm_instance
    
    if config_path is None:
        config_path = os.getenv("MODEL_CONFIG", "configs/models/local/gemma/v2/cpu/2b-cpu-only.yaml")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    full_config_path = os.path.join(project_root, config_path)
    
    if not os.path.exists(full_config_path):
        raise FileNotFoundError(f"Config file not found: {full_config_path}")
    
    with open(full_config_path, "r") as f:
        config = yaml.safe_load(f) or {}
    
    llm_instance = LLMFactory.create(config)
    return llm_instance

@chat_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Chat completions endpoint compatible with OpenAI format"""
    try:
        data = request.get_json(silent=True) or {}
        
        prompt = data.get("prompt")
        
        if not prompt:
            messages = data.get("messages", [])
            if isinstance(messages, list) and len(messages) > 0:
                prompt = messages[-1].get("content")
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        config_path = data.get("config_path")
        instance = get_llm_instance(config_path)
        
        # Get generation parameters
        params = {
            "temperature": data.get("temperature", 0.7),
            "top_p": data.get("top_p", 0.95),
            "max_tokens": data.get("max_tokens", 512)
        }
        
        stream = data.get("stream", False)
        
        if stream:
            from flask import Response
            import json
            
            def generate_stream():
                try:
                    for chunk in instance.stream_generate(prompt, **params):
                        if chunk:
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}, 'index': 0, 'finish_reason': None}]})}\n\n"
                    yield f"data: {json.dumps({'choices': [{'delta': {}, 'index': 0, 'finish_reason': 'stop'}]})}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    yield "data: [DONE]\n\n"

            return Response(generate_stream(), mimetype='text/event-stream')

        response = instance.generate(
            prompt,
            **params
        )
        
        return jsonify({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop",
                "index": 0
            }]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint"""
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get("prompt")
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        config_path = data.get("config_path")
        instance = get_llm_instance(config_path)
        response = instance.generate(prompt)
        
        return jsonify({
            "response": response,
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
