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
