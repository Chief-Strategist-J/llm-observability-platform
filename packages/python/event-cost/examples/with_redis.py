from features.cost_ledger.ledger import CostLedger
from features.cost_ledger.backends.redis import RedisBackend

ledger = CostLedger(backend=RedisBackend(redis_url="redis://localhost:6379/0"))

ledger.record(
    model="gpt-4",
    provider="openai",
    prompt_tokens=100,
    completion_tokens=200,
    org_id="test-org",
    project_id="test-proj"
)

print(ledger.total_cost_usd(org_id="test-org", window="24h"))
