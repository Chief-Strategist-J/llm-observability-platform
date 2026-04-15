from flask import Blueprint, jsonify, request
import os
from pathlib import Path

model_bp = Blueprint('model', __name__)

@model_bp.route('/api/model/download-progress', methods=['GET'])
def download_progress():
    try:
        model_id = request.args.get('model_id', 'google/gemma-2-2b-it')
        cache_name = model_id.replace('--', '--')
        cache_path = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{cache_name}"
        
        if not cache_path.exists():
            return jsonify({
                "status": "not_started",
                "size_gb": 0,
                "path": str(cache_path)
            })
        
        total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
        size_gb = total_size / (1024**3)
        
        return jsonify({
            "status": "downloading" if size_gb < 5 else "complete",
            "size_gb": round(size_gb, 2),
            "path": str(cache_path)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_bp.route('/api/model/info', methods=['GET'])
def model_info():
    try:
        config_path = request.args.get('config_path', 'configs/models/local/gemma/v2/cpu/2b.yaml')
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        full_config_path = os.path.join(project_root, config_path)
        
        if not os.path.exists(full_config_path):
            return jsonify({"error": "Config file not found"}), 404
        
        import yaml
        with open(full_config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        
        model_config = config.get('model', {})
        
        return jsonify({
            "model_id": model_config.get('id'),
            "name": model_config.get('name'),
            "version": model_config.get('version'),
            "size": model_config.get('size'),
            "provider": model_config.get('provider'),
            "backend": model_config.get('backend'),
            "accelerator": model_config.get('resources', {}).get('accelerator'),
            "quantization": model_config.get('quantization'),
            "parameters": model_config.get('parameters', {})
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
