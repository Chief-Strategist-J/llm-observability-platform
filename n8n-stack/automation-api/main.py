from fastapi import FastAPI, WebSocket, Request
import os, httpx

app = FastAPI()
N8N_BASE = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_WEBHOOK_PATH = os.getenv("N8N_WEBHOOK_PATH", "/webhook/automation")

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/trigger")
async def trigger(payload: dict):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{N8N_BASE}{N8N_WEBHOOK_PATH}", json=payload)
        return {"status": r.status_code, "body": r.text}

@app.post("/webhook/events")
async def webhook(payload: dict):
    async with httpx.AsyncClient(timeout=10) as c:
        await c.post(f"{N8N_BASE}{N8N_WEBHOOK_PATH}", json=payload)
    return {"received": True}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            async with httpx.AsyncClient(timeout=5) as c:
                try:
                    await c.post(f"{N8N_BASE}{N8N_WEBHOOK_PATH}", json={"ws": data})
                except Exception:
                    pass
            await ws.send_text(data)
    except Exception:
        await ws.close()
