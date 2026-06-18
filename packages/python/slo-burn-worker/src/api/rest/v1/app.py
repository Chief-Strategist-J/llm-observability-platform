from typing import Any
from fastapi import FastAPI, HTTPException
from api.index import health as get_health, trigger_workflow as trigger_slo_workflow
from prometheus_client import make_asgi_app

app = FastAPI(title="Temporal SLO Burn Worker API", version="1.0.0")
app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health() -> dict[str, Any]:
    try:
        return await get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger")
async def trigger_workflow() -> dict[str, Any]:
    try:
        res = await trigger_slo_workflow()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
