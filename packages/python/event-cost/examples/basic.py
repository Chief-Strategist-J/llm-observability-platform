from event_cost import CostLedger

def run_example():
    ledger = CostLedger()
    ledger.record(
        model="gpt-4",
        provider="openai",
        prompt_tokens=150,
        completion_tokens=300,
        org_id="my-org",
        project_id="default-project",
        service_name="chat-api",
        user_id="user-123"
    )
    total = ledger.total_cost_usd(org_id="my-org", window="24h")
    print(f"Total cost: ${total:.6f} USD")

if __name__ == "__main__":
    run_example()
