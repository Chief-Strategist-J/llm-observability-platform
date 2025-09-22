from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx, os

app = FastAPI(title="Automation API", version="1.0.0")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_API_KEY  = os.getenv("N8N_API_KEY", "")

def api_headers():
    if not N8N_API_KEY:
        raise RuntimeError("N8N_API_KEY not set")
    return {"X-N8N-API-KEY": N8N_API_KEY}

@app.get("/healthz")
async def health():
    return {"ok": True}

@app.get("/n8n/executions")
async def list_executions(limit: int = 20, lastId: int | None = None):
    params = {"limit": limit}
    if lastId is not None:
        params["lastId"] = lastId
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{N8N_BASE_URL}/api/v1/executions",
                             headers=api_headers(), params=params)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return JSONResponse(r.json())

@app.post("/n8n/trigger/{webhook_path:path}")
async def trigger(webhook_path: str, request: Request):
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "application/json")}
    url = f"{N8N_BASE_URL}/webhook/{webhook_path}".rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, content=body, headers=headers)
        return JSONResponse(status_code=r.status_code, content=r.text)
