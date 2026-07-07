from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from api.index import health as get_health, trigger_workflow as trigger_forecast_workflow
from prometheus_client import make_asgi_app

app = FastAPI(title="Temporal Forecast Worker API", version="1.0.0")
app.mount("/metrics", make_asgi_app())

class TriggerRequest(BaseModel):
    lookback_hours: int = Field(default=168, ge=1)
    min_history_hours: int = Field(default=48, ge=1)

@app.get("/health")
async def health() -> dict:
    try:
        return await get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger")
async def trigger_workflow(request: TriggerRequest | None = None) -> dict:
    try:
        lookback = request.lookback_hours if request else 168
        min_hist = request.min_history_hours if request else 48
        res = await trigger_forecast_workflow(lookback_hours=lookback, min_history_hours=min_hist)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
