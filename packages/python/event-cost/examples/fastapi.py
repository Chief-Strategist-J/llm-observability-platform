from fastapi import FastAPI, HTTPException
from features.cost_ledger.ledger import CostLedger

app = FastAPI(title="Cost Engine Demo Service")
ledger = CostLedger()


@app.post("/chat/completions")
def chat_completion(payload: dict):
    model = payload.get("model", "gpt-4")
    provider = payload.get("provider", "openai")
    prompt_tokens = payload.get("prompt_tokens", 100)
    completion_tokens = payload.get("completion_tokens", 50)
    org_id = payload.get("org_id", "default-org")

    ledger.record(
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        org_id=org_id,
        service_name="fastapi-demo",
    )

    cost_usd = ledger.total_cost_usd(org_id=org_id, window="24h")
    budget_rem = ledger.budget_remaining(org_id=org_id)

    return {
        "status": "ok",
        "recorded_tokens": prompt_tokens + completion_tokens,
        "total_cost_24h_usd": cost_usd,
        "budget_remaining_usd": budget_rem,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
