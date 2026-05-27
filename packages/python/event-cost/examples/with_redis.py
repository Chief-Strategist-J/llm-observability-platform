from event_cost import CostLedger
from event_cost.backends.redis import RedisBackend

def run_redis_example():
    backend = RedisBackend(redis_url="redis://localhost:6379/0")
    ledger = CostLedger(backend=backend)
    ledger.record(
        model="gpt-4",
        provider="openai",
        prompt_tokens=200,
        completion_tokens=400,
        org_id="corporate-org",
        project_id="enterprise-project",
        service_name="payment-service",
        user_id="user-999"
    )
    total = ledger.total_cost_usd(org_id="corporate-org", window="24h")
    print(f"Redis cost: ${total:.6f} USD")

if __name__ == "__main__":
    run_redis_example()
