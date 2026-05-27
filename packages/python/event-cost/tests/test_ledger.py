import os
import tempfile
import pytest
from event_cost import CostLedger
from event_cost.backends.sqlite import SQLiteBackend

def test_sqlite_backend_record_and_query():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        backend = SQLiteBackend(db_path=db_path)
        ledger = CostLedger(backend=backend)
        
        ledger.record(
            model="gpt-4",
            provider="openai",
            prompt_tokens=100,
            completion_tokens=200,
            org_id="test-org",
            project_id="test-proj"
        )
        
        total = ledger.total_cost_usd(org_id="test-org", window="24h")
        assert total == 0.015
        
        ledger.set_budget(org_id="test-org", budget_usd=10.0, project_id="test-proj")
        rem = ledger.budget_remaining(org_id="test-org", project_id="test-proj")
        assert rem == 9.985

def test_redis_backend_mock(monkeypatch):
    from unittest.mock import MagicMock
    import redis as redis_lib
    from event_cost.backends.redis import RedisBackend

    mock_client = MagicMock()
    mock_pipeline = MagicMock()
    mock_client.pipeline.return_value = mock_pipeline
    
    mock_script = MagicMock()
    mock_script.sha = "mock-sha"
    mock_client.register_script.return_value = mock_script

    monkeypatch.setattr(redis_lib, "from_url", lambda url: mock_client)

    backend = RedisBackend("redis://localhost:6379/0")
    
    backend.record(
        span=MagicMock(
            org_id="test-org",
            project_id="test-proj",
            service_name="test-service",
            model="gpt-4",
            provider="openai",
            prompt_tokens=100,
            completion_tokens=200,
            user_id="test-user",
            estimated_tokens=150,
        ),
        cost_usd_micro=15000
    )

    assert mock_pipeline.evalsha.call_count > 0
    
    mock_script.return_value = "8000"
    total = backend.query_total("test-org", "24h")
    assert total == 8000
    
    mock_client.get.return_value = b"10000000"
    budget = backend.get_budget("test-org", "test-proj")
    assert budget == 10000000
    
    backend.set_budget("test-org", "test-proj", 10000000)
    mock_client.set.assert_called_with("budget:tb:test-org:test-proj", "10000000")
