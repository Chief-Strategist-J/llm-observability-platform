from pathlib import Path
from typing import Dict, Tuple

from flask import Blueprint, jsonify, request
import os
import yaml

from services.llm.registry import PROVIDER_REGISTRY
from services.llm.factory import LLMFactory
from services.shared.model_registry import model_registry

model_bp = Blueprint('model', __name__)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _safe_config_path(config_path: str) -> Tuple[Path, str | None]:
    path_str = (config_path or '').strip()
    if not path_str:
        return Path(), 'config_path is required'

    full_path = (_PROJECT_ROOT / path_str).resolve()
    try:
        full_path.relative_to(_PROJECT_ROOT)
    except ValueError:
        return Path(), 'config_path must be inside project directory'

    if not full_path.exists():
        return Path(), 'Config file not found'

    if full_path.suffix.lower() not in {'.yaml', '.yml'}:
        return Path(), 'config_path must point to a yaml file'

    return full_path, None


def _validate_cloudflare_env(model_config: Dict[str, object]) -> Dict[str, object]:
    account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID', '').strip()
    api_token = os.getenv('CLOUDFLARE_API_TOKEN', '').strip()
    base_url = os.getenv('CLOUDFLARE_BASE_URL', '').strip()

    issues = []
    if not api_token:
        issues.append('Missing CLOUDFLARE_API_TOKEN')
    if not base_url and not account_id:
        issues.append('Missing CLOUDFLARE_ACCOUNT_ID (required when CLOUDFLARE_BASE_URL is unset)')

    model_id = str(model_config.get('id') or '').strip()
    if not model_id:
        issues.append('Cloudflare model.id must be provided')

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'effective_base_url': base_url or f'https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1',
    }

def _resolve_model_record(data: Dict[str, object]):
    model_key = str(data.get('model_key') or '').strip()
    if model_key:
        return model_registry.get_by_key(model_key), None

    config_path = str(data.get('config_path') or '').strip()
    if config_path:
        full_config_path, error = _safe_config_path(config_path)
        if error:
            return None, error
        with open(full_config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        return {'key': config_path, 'config': config}, None

    return None, 'Provide either model_key or config_path'


def _build_generation_params(data: Dict[str, object]) -> Dict[str, object]:
    return {
        'temperature': data.get('temperature', 0.7),
        'top_p': data.get('top_p', 0.95),
        'max_tokens': data.get('max_tokens', 512),
    }


def _resolve_query_config(data: Dict[str, object]):
    config = data.get('config')
    if isinstance(config, dict):
        return config, {'key': 'inline'}

    record, error = _resolve_model_record(data)
    if error:
        return None, {'error': error}
    if not record:
        return None, {'error': 'Model config not found'}

    return record.get('config') or {}, record



@model_bp.route('/api/model/download-progress', methods=['GET'])
def download_progress():
    try:
        model_id = request.args.get('model_id', 'google/gemma-2-2b-it')
        cache_name = model_id.replace('--', '--')
        cache_path = Path.home() / '.cache' / 'huggingface' / 'hub' / f'models--{cache_name}'

        if not cache_path.exists():
            return jsonify({
                'status': 'not_started',
                'size_gb': 0,
                'path': str(cache_path)
            })

        total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
        size_gb = total_size / (1024**3)

        return jsonify({
            'status': 'downloading' if size_gb < 5 else 'complete',
            'size_gb': round(size_gb, 2),
            'path': str(cache_path)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@model_bp.route('/api/model/info', methods=['GET'])
def model_info():
    try:
        payload = {
            'model_key': request.args.get('model_key', ''),
            'config_path': request.args.get('config_path', 'configs/models/local/gemma/v2/cpu/2b.yaml'),
        }
        record, error = _resolve_model_record(payload)
        if error:
            return jsonify({'error': error}), 400
        if not record:
            return jsonify({'error': 'Model config not found'}), 404

        config = record.get('config', {})
        model_config = config.get('model', {})

        return jsonify({
            'key': record.get('key'),
            'source': record.get('source', model_registry.backend),
            'model_id': model_config.get('id'),
            'name': model_config.get('name'),
            'version': model_config.get('version'),
            'size': model_config.get('size'),
            'provider': model_config.get('provider'),
            'backend': model_config.get('backend'),
            'accelerator': model_config.get('resources', {}).get('accelerator'),
            'quantization': model_config.get('quantization'),
            'parameters': model_config.get('parameters', {})
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500




@model_bp.route('/api/model/catalog', methods=['GET'])
def list_model_catalog():
    provider = request.args.get('provider')
    limit = request.args.get('limit', 100)
    offset = request.args.get('offset', 0)

    try:
        total, items = model_registry.list_models(provider=provider, limit=int(limit), offset=int(offset))
        return jsonify({
            'backend': model_registry.backend,
            'total': total,
            'count': len(items),
            'items': items,
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@model_bp.route('/api/model/catalog/sync', methods=['POST'])
def sync_model_catalog_to_db():
    if model_registry.backend != 'mongodb':
        return jsonify({'error': 'sync is only available when MODEL_REGISTRY_BACKEND=mongodb'}), 400

    try:
        records = model_registry.build_records_from_filesystem()
        upserted = model_registry.upsert_many(records)
        return jsonify({
            'status': 'success',
            'records': len(records),
            'upserted_or_updated': upserted,
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500



@model_bp.route('/api/model/query', methods=['POST'])
def query_model():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get('prompt') or '').strip()
    if not prompt:
        return jsonify({'error': 'prompt is required'}), 400

    config, meta = _resolve_query_config(data)
    if config is None:
        return jsonify({'error': meta.get('error', 'Unable to resolve model config')}), 400

    try:
        llm = LLMFactory.create(config)
        response = llm.generate(prompt, **_build_generation_params(data))
        model = (config or {}).get('model', {})

        return jsonify({
            'response': response,
            'model': {
                'key': meta.get('key'),
                'id': model.get('id'),
                'provider': model.get('provider'),
                'name': model.get('name'),
            },
            'status': 'success',
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@model_bp.route('/api/model/query/stream', methods=['POST'])
def query_model_stream():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get('prompt') or '').strip()
    if not prompt:
        return jsonify({'error': 'prompt is required'}), 400

    config, meta = _resolve_query_config(data)
    if config is None:
        return jsonify({'error': meta.get('error', 'Unable to resolve model config')}), 400

    try:
        llm = LLMFactory.create(config)
        tokens = list(llm.stream_generate(prompt, **_build_generation_params(data)))
        model = (config or {}).get('model', {})

        return jsonify({
            'tokens': tokens,
            'response': ''.join(tokens),
            'model': {
                'key': meta.get('key'),
                'id': model.get('id'),
                'provider': model.get('provider'),
                'name': model.get('name'),
            },
            'status': 'success',
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@model_bp.route('/api/model/providers', methods=['GET'])
def list_providers():
    return jsonify({
        'providers': sorted(PROVIDER_REGISTRY.keys())
    })


@model_bp.route('/api/model/validate', methods=['POST'])
def validate_model_config():
    data = request.get_json(silent=True) or {}

    config = data.get('config')
    if config is None:
        try:
            record, error = _resolve_model_record(data)
            if error:
                return jsonify({'valid': False, 'errors': [error]}), 400
            if not record:
                return jsonify({'valid': False, 'errors': ['Model config not found']}), 404
            config = record.get('config')
        except Exception as exc:
            return jsonify({'valid': False, 'errors': [f'Failed to resolve config: {exc}']}), 400

    model_config = config.get('model') if isinstance(config, dict) else None
    if not isinstance(model_config, dict):
        return jsonify({'valid': False, 'errors': ['config.model must be an object']}), 400

    provider = str(model_config.get('provider') or '').strip()
    if not provider:
        return jsonify({'valid': False, 'errors': ['model.provider is required']}), 400
    if provider not in PROVIDER_REGISTRY:
        return jsonify({'valid': False, 'errors': [f'Unsupported provider: {provider}']}), 400

    response = {
        'valid': True,
        'provider': provider,
        'warnings': [],
    }

    if provider == 'cloudflare':
        cloudflare_validation = _validate_cloudflare_env(model_config)
        response['cloudflare'] = cloudflare_validation
        if not cloudflare_validation['valid']:
            response['valid'] = False

    return jsonify(response), 200 if response['valid'] else 400
