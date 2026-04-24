from unittest.mock import patch

from pathlib import Path


def test_model_providers_includes_cloudflare(client):
    response = client.get('/api/model/providers')
    assert response.status_code == 200
    data = response.get_json()
    assert 'providers' in data
    assert 'cloudflare' in data['providers']


def test_model_validate_inline_cloudflare_success(client, monkeypatch):
    monkeypatch.setenv('CLOUDFLARE_API_TOKEN', 'token')
    monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'account-123')

    response = client.post('/api/model/validate', json={
        'config': {
            'model': {
                'provider': 'cloudflare',
                'id': '@cf/meta/llama-3.1-8b-instruct'
            }
        }
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['valid'] is True
    assert data['provider'] == 'cloudflare'
    assert data['cloudflare']['valid'] is True


def test_model_validate_cloudflare_missing_token(client, monkeypatch):
    monkeypatch.delenv('CLOUDFLARE_API_TOKEN', raising=False)
    monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'account-123')

    response = client.post('/api/model/validate', json={
        'config': {
            'model': {
                'provider': 'cloudflare',
                'id': '@cf/meta/llama-3.1-8b-instruct'
            }
        }
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['valid'] is False
    assert 'Missing CLOUDFLARE_API_TOKEN' in data['cloudflare']['issues']


def test_model_validate_rejects_path_traversal(client):
    response = client.post('/api/model/validate', json={'config_path': '../../etc/passwd'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['valid'] is False


def test_model_validate_accepts_config_path(client):
    config_path = 'configs/models/local/gemma/v2/cpu/2b-cpu-only.yaml'
    response = client.post('/api/model/validate', json={'config_path': config_path})
    assert response.status_code == 200
    data = response.get_json()
    assert data['provider'] == 'local'


def test_model_info_rejects_non_yaml(client, tmp_path, monkeypatch):
    from services.api.routes import model as model_route

    txt_file = tmp_path / 'bad.txt'
    txt_file.write_text('just text')

    monkeypatch.setattr(model_route, '_PROJECT_ROOT', tmp_path)
    rel_path = str(Path('bad.txt'))

    response = client.get('/api/model/info', query_string={'config_path': rel_path})
    assert response.status_code == 400
    assert 'yaml' in response.get_json()['error']


def test_model_catalog_lists_items(client):
    response = client.get('/api/model/catalog', query_string={'provider': 'cloudflare', 'limit': 5})
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] <= 5
    assert data['total'] >= data['count']
    assert data['backend'] in {'filesystem', 'mongodb'}


def test_model_catalog_sync_requires_mongodb(client):
    response = client.post('/api/model/catalog/sync')
    data = response.get_json()
    if data.get('status') == 'success':
        assert response.status_code == 200
    else:
        assert response.status_code == 400
        assert 'MODEL_REGISTRY_BACKEND=mongodb' in data['error']


def test_model_info_supports_model_key(client):
    response = client.get('/api/model/info', query_string={'model_key': 'catalog/cloudflare/meta/llama-3.1-8b-instruct'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['provider'] == 'cloudflare'


def test_model_validate_supports_model_key(client):
    response = client.post('/api/model/validate', json={'model_key': 'catalog/cloudflare/meta/llama-3.1-8b-instruct'})
    assert response.status_code in {200, 400}  # depends on cloudflare env presence
    data = response.get_json()
    assert data['provider'] == 'cloudflare'


class _FakeQueryLLM:
    def generate(self, prompt, **kwargs):
        return f"echo:{prompt}"

    def stream_generate(self, prompt, **kwargs):
        yield "hello"
        yield " world"


def test_model_query_returns_response(client):
    with patch('services.api.routes.model.LLMFactory.create', return_value=_FakeQueryLLM()) as mock_create:
        response = client.post('/api/model/query', json={
            'prompt': 'test prompt',
            'model_key': 'catalog/cloudflare/meta/llama-3.1-8b-instruct'
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['response'] == 'echo:test prompt'
    assert data['model']['provider'] == 'cloudflare'
    mock_create.assert_called_once()


def test_model_query_requires_prompt(client):
    response = client.post('/api/model/query', json={'model_key': 'catalog/cloudflare/meta/llama-3.1-8b-instruct'})
    assert response.status_code == 400
    assert 'prompt is required' in response.get_json()['error']


def test_model_query_stream_returns_tokens(client):
    with patch('services.api.routes.model.LLMFactory.create', return_value=_FakeQueryLLM()):
        response = client.post('/api/model/query/stream', json={
            'prompt': 'stream this',
            'model_key': 'catalog/cloudflare/meta/llama-3.1-8b-instruct'
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data['tokens'] == ['hello', ' world']
    assert data['response'] == 'hello world'


def test_model_query_invalid_model_returns_error(client):
    response = client.post('/api/model/query', json={
        'prompt': 'hello',
        'model_key': 'catalog/cloudflare/does-not-exist'
    })
    assert response.status_code == 400
    assert 'Model config not found' in response.get_json()['error']
