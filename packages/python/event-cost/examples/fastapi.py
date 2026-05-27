from fastapi import FastAPI, Request
from event_cost import CostLedger

app = FastAPI()
ledger = CostLedger()

@app.middleware("http")
async def track_llm_cost(request: Request, call_next):
    response = await call_next(request)
    prompt_tokens = getattr(request.state, "prompt_tokens", 0)
    completion_tokens = getattr(request.state, "completion_tokens", 0)
    model = getattr(request.state, "model", "gpt-4o")
    provider = getattr(request.state, "provider", "openai")
    
    if prompt_tokens > 0 or completion_tokens > 0:
        ledger.record(
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            org_id="fastapi-org",
            project_id="main",
            service_name="gateway",
            user_id="user_123"
        )
    return response

@app.post("/chat")
async def chat(request: Request):
    request.state.prompt_tokens = 15
    request.state.completion_tokens = 35
    request.state.model = "gpt-4o"
    request.state.provider = "openai"
    return {"message": "Hello world"}

@app.get("/metrics")
def get_metrics():
    total = ledger.total_cost_usd(org_id="fastapi-org", window="24h")
    return {"total_cost_usd_24h": total}
