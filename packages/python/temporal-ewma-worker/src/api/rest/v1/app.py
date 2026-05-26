from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from api.index import health as get_health, trigger_workflow as trigger_ewma_workflow

app = FastAPI(title="Temporal EWMA Worker API", version="1.0.0")


class TriggerRequest(BaseModel):
    force_hour: int | None = Field(default=None, ge=0, le=167)


@app.get("/health")
async def health() -> dict:
    try:
        return await get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger")
async def trigger_workflow(request: TriggerRequest | None = None) -> dict:
    try:
        force_hour = request.force_hour if request else None
        res = await trigger_ewma_workflow(force_hour=force_hour)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
