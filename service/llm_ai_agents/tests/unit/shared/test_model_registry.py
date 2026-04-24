from services.shared.model_registry import ModelRegistryRepository


def test_model_registry_filesystem_get_by_key_returns_record(monkeypatch):
    monkeypatch.setenv('MODEL_REGISTRY_BACKEND', 'filesystem')
    repo = ModelRegistryRepository()

    record = repo.get_by_key('catalog/cloudflare/meta/llama-3.1-8b-instruct')
    assert record is not None
    assert record['provider'] == 'cloudflare'
    assert record['id']


def test_model_registry_filesystem_list_models_filter(monkeypatch):
    monkeypatch.setenv('MODEL_REGISTRY_BACKEND', 'filesystem')
    repo = ModelRegistryRepository()

    total, items = repo.list_models(provider='cloudflare', limit=10, offset=0)
    assert total >= 1
    assert len(items) <= 10
    assert all(item.get('provider') == 'cloudflare' for item in items)


def test_model_registry_build_records_from_filesystem(monkeypatch):
    monkeypatch.setenv('MODEL_REGISTRY_BACKEND', 'filesystem')
    repo = ModelRegistryRepository()

    records = repo.build_records_from_filesystem('configs/models/cloudflare')
    assert len(records) >= 1
    assert all('key' in r and 'config' in r for r in records)
