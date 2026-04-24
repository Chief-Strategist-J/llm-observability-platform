from pathlib import Path

from services.shared.model_registry import ModelRegistryRepository


def test_cloudflare_catalog_ids_are_unique(monkeypatch):
    monkeypatch.setenv('MODEL_REGISTRY_BACKEND', 'filesystem')
    repo = ModelRegistryRepository()

    records = repo.build_records_from_filesystem()
    identities = [(r.get('provider'), r.get('id')) for r in records]

    assert len(identities) == len(set(identities))


def test_generated_seed_files_exist_and_nonempty():
    sql_path = Path('service/llm_ai_agents/scripts/db/seed_model_catalog.postgres.sql')
    mongo_path = Path('service/llm_ai_agents/scripts/db/seed_model_catalog.mongo.js')

    assert sql_path.exists()
    assert mongo_path.exists()
    assert sql_path.read_text().strip()
    assert mongo_path.read_text().strip()


def test_generated_postgres_seed_contains_upsert():
    sql_path = Path('service/llm_ai_agents/scripts/db/seed_model_catalog.postgres.sql')
    sql = sql_path.read_text()

    assert 'CREATE TABLE IF NOT EXISTS model_catalog' in sql
    assert 'ON CONFLICT (key) DO UPDATE SET' in sql
    assert 'INSERT INTO model_catalog' in sql


def test_filesystem_catalog_has_required_fields(monkeypatch):
    monkeypatch.setenv('MODEL_REGISTRY_BACKEND', 'filesystem')
    repo = ModelRegistryRepository()

    total, items = repo.list_models(limit=500, offset=0)
    assert total >= 1
    assert all(item.get('provider') for item in items)
    assert all(item.get('id') for item in items)
