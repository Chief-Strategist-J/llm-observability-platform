from fastapi import FastAPI, HTTPException
from api.index import health as get_health, trigger_checkpoint as trigger_checkpoint_wf
from prometheus_client import make_asgi_app

app = FastAPI(title="Latency Baseline Worker API", version="1.0.0")
app.mount("/metrics", make_asgi_app())

@app.get("/health")
async def health() -> dict:
    try:
        return await get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger/checkpoint")
async def trigger_checkpoint() -> dict:
    try:
        return await trigger_checkpoint_wf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
