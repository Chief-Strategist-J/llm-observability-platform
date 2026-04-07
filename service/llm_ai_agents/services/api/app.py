from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@app.route('/setup', methods=['POST'])
def setup():
    try:
        res = subprocess.run(['bash', 'scripts/setup/bootstrap.sh'], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    model_id = request.json.get('model_id')
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    try:
        res = subprocess.run(['bash', 'scripts/setup/download_model.sh', model_id], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

@app.route('/start', methods=['POST'])
def start():
    config_path = request.json.get('config_path')
    if not config_path:
        return jsonify({"error": "config_path required"}), 400
    try:
        res = subprocess.run(['bash', 'scripts/dev/start_model.sh', config_path], cwd=BASE_DIR, capture_output=True, text=True)
        return jsonify({"status": "success" if res.returncode == 0 else "error", "stdout": res.stdout, "stderr": res.stderr})
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
