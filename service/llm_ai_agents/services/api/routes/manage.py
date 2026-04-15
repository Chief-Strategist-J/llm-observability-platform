from flask import Blueprint, request, jsonify
import subprocess
import os

manage_bp = Blueprint('manage', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@manage_bp.route('/setup', methods=['POST'])
def setup():
    try:
        res = subprocess.run(['bash', 'scripts/setup/bootstrap.sh'], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

@manage_bp.route('/download', methods=['POST'])
def download():
    model_id = request.json.get('model_id')
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    try:
        res = subprocess.run(['bash', 'scripts/setup/download_model.sh', model_id], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

@manage_bp.route('/start', methods=['POST'])
def start():
    config_path = request.json.get('config_path')
    if not config_path:
        return jsonify({"error": "config_path required"}), 400
    try:
        res = subprocess.run(['bash', 'scripts/dev/start_model.sh', config_path], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500
