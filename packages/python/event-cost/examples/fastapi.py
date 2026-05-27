from fastapi import FastAPI, Request
from event_cost import CostLedger

app = FastAPI()
ledger = CostLedger()

@app.middleware("http")
async def track_llm_cost(request: Request, call_next):
    response = await call_next(request)
    ledger.record(
        model="gpt-4o",
        provider="openai",
        prompt_tokens=100,
        completion_tokens=200,
        org_id="fastapi-org",
        project_id="main",
        service_name="gateway",
        user_id="anonymous"
    )
    return response

@app.get("/metrics")
def get_metrics():
    total = ledger.total_cost_usd(org_id="fastapi-org", window="24h")
    return {"total_cost_usd_24h": total}
